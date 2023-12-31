from cmath import nan
from lib2to3.pgen2.pgen import DFAState
import praw
import pandas as pd
import numpy as np
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import re
import string
import os

# set up
def prawSetUp():
    reddit = praw.Reddit(client_id='id', client_secret='secret', user_agent='agent') # update these header values with your own
    return reddit

# reddit scraping and dataframe creation
def redditDf(reddit, limitN):
    df_ffposts = pd.DataFrame(columns=['id', 'title', 'subreddit', 'created', 'num_comments'])
    hot_posts = reddit.subreddit('fantasyfootball')

    for post in hot_posts.hot(limit=limitN):
        df_ffposts = df_ffposts.append({'id' : post.id, 'title' : post.title, 'subreddit' : post.subreddit, 'created' : post.created, 'num_comments' : post.num_comments}, ignore_index=True)
    df_ffposts['player'] = ''
    df_ffposts.loc[:,'player'] = df_ffposts.loc[:,'title']
    df_ffposts['post_sent'] = ''
    df_ffposts['comment_sent'] = ''
    print(df_ffposts.shape)
    return df_ffposts

# Proper noun analysis. Grab all capitalized words in a sentence that have a capitalized word following them
# Place them in a temporary dataframe and then remove all rows that do not appear in the player list
# If only one player is mentioned in a post then return that players name
def nnpFinder(txt):
    global playerList
    sentences = re.split(r'\?|!|\.|,|\'|:|;|-|\]|\[|\(|\)', txt)
    df_temp = pd.DataFrame(columns=['Nouns'])
    for sentence in sentences:
        words = sentence.split()
        if len(sentence) > 0: #maybe change this to being greater than or equal to the shortest name of an active player, including a space
            for i in range(len(words)):
                if i + 1 < len(words):
                    if words[i][0].isupper() & words[i+1][0].isupper():
                        word = words[i] + ' ' + words[i+1]
                        df_temp = df_temp.append({'Nouns' : word}, ignore_index=True)
    df_temp = df_temp[df_temp['Nouns'].isin(playerList)]
    if df_temp.shape == (1,1):
        return df_temp.iloc[0]['Nouns']
    else:
        return 'N/A'   

# sentiment analysis
def postVader(df_ffposts, colText, colSent):
    for ind in df_ffposts.index:
        sid_obj = SentimentIntensityAnalyzer()
        sentiment_dict = sid_obj.polarity_scores(df_ffposts[colText][ind])
        df_ffposts[colSent][ind] = sentiment_dict.get('compound')

    return df_ffposts         

# grab all comments for a post and return a df containing the comments. actually return an average sentiment
def getComments(df_ffposts, reddit, colCommSent):
    for ind in df_ffposts.index:
        df_comm = pd.DataFrame(columns=['Comment'])
        currPost = reddit.submission(id=df_ffposts['id'][ind])
        for comment in currPost.comments: 
            df_comm = df_comm.append({'Comment' : comment.body}, ignore_index=True)
        df_comm['commSent'] = ''
        if df_comm.shape[0] > 0:
            df_comm = postVader(df_comm, 'Comment', 'commSent')
            avgSent = df_comm['commSent'].mean()
        else:
            avgSent = 0
        df_ffposts[colCommSent][ind] = avgSent
    return df_ffposts

# read txt files containing active player names into dataframe
def readFolder(path):
    global playerList 
    playerList = []
    df_players = pd.DataFrame(columns=['lastName', 'firstName', 'position', 'teamAndCollege'])
    for file in os.listdir(path):
        df_pTemp = pd.read_csv(path + file, skiprows=1, names=['lastName', 'firstName'], sep=', ', header=None)
        df_pTemp['position'] = df_pTemp['firstName'].copy()
        df_pTemp['teamAndCollege'] = df_pTemp['firstName'].copy()
        if df_pTemp.shape[0] > 0:
            df_pTemp['firstName'] = df_pTemp['firstName'].apply(lambda x: x.split()[0])
            df_pTemp['position'] = df_pTemp['position'].apply(lambda x: x.split()[1])
            df_pTemp['teamAndCollege'] = df_pTemp['teamAndCollege'].apply(lambda x: x.split()[2:])
            df_players = df_players.append(df_pTemp)
    return df_players

def main():
    global playerList
    path = 'Players/'
    limitN = 50000

    df_players = readFolder(path)
    df_players['player'] = df_players['firstName'] + ' ' + df_players['lastName']
    playerNames = df_players['player'].squeeze()
    playerList = playerNames.tolist()

    reddit = prawSetUp()
    df_ffposts = redditDf(reddit, limitN)
    df_ffposts['player'] = df_ffposts['player'].apply(nnpFinder)
    df_ffposts.drop(df_ffposts[df_ffposts['player'] == 'N/A'].index, inplace=True)
    df_ffposts.reset_index(drop=True)
    df_ffposts = postVader(df_ffposts, 'title', 'post_sent')
    df_ffposts = getComments(df_ffposts, reddit, 'comment_sent')
    df_ffposts = df_ffposts.merge(df_players,how='inner',on='player')
    df_ffposts.to_csv('Output.csv', index=False)
    print(df_ffposts)

main()



