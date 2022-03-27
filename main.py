# import
import os
import random
import nltk
nltk.download('wordnet')
import re
from nltk.corpus import wordnet
import discord
from dotenv import load_dotenv
import wikipedia
import numpy as np
import pandas as pd
from fuzzywuzzy import process

wikipedia.set_lang("en")
load_dotenv()
TOKEN = os.getenv('TOKEN')
client = discord.Client()

#Import the correlation matrix
MatrixCorr = pd.read_pickle(r"corrMatrix.pkl")
bookList = MatrixCorr.index

def closestBook(mystring):
    highest = process.extractOne(mystring,bookList)
    return highest

def recommendBook(myBookList):
    myRatings = pd.DataFrame(columns=['book', 'rating'])
    
    for book in myBookList:
        myRatings = myRatings.append({'book':book, 'rating':5}, ignore_index=True)
    myRatings = myRatings.set_index('book')
    same_Candidates = pd.Series(dtype='float64')
    
    for i in range(0, len(myRatings.index)):
        # retrieve similar books to this one that I rated
        same_books = MatrixCorr[myRatings.index[i]].dropna()
        # scale its similarity by how well I rated this book
        same_books = same_books.map(lambda x: x * myRatings.iloc[i]['rating'])
        # add the score to the list of similar candidates
        same_Candidates = same_Candidates.append(same_books)
        
    same_Candidates = same_Candidates.groupby(same_Candidates.index).sum()
    same_Candidates = same_Candidates.drop(same_Candidates.loc[same_Candidates.index.isin(myRatings.index)].index)

    same_Candidates.sort_values(inplace = True, ascending = False)
    same_Candidates = same_Candidates[0:10].index
    return same_Candidates

# Building a list of Keywords
list_words=['hello','help','information','thank','thanks']
list_syn={}

for word in list_words:
    synonyms=[]
    for syn in wordnet.synsets(word):
        for lem in syn.lemmas():
            # Remove any special characters from synonym strings
            lem_name = re.sub('[^a-zA-Z0-9 \n\.]', ' ', lem.name())
            synonyms.append(lem_name)
    list_syn[word]=set(synonyms)
#print (list_syn)

# Building dictionary of Intents & Keywords
keywords={}
keywords_dict={}


# Defining a new key in the keywords dictionary

keywords['greet']=[]
for synonym in list(list_syn['hello']):
    keywords['greet'].append('.*\\b'+synonym+'\\b.*')

keywords['help']=[]
for synonym in list(list_syn['help']):
    keywords['help'].append('.*\\b'+synonym+'\\b.*')

keywords['info']=[]
for synonym in list(list_syn['information']):
    keywords['info'].append('.*\\b'+synonym+'\\b.*')

keywords['thank']=[]
for synonym in list(list_syn['thank']):
    keywords['thank'].append('.*\\b'+synonym+'\\b.*')

keywords['thanks']=[]
for synonym in list(list_syn['thanks']):
    keywords['thanks'].append('.*\\b'+synonym+'\\b.*')


keywords['feelings']=[]
keywords['feelings'].append('.*\\bhow are\\b.*')


for intent, keys in keywords.items():
    keywords_dict[intent]=re.compile('|'.join(keys))


help_text = '\n\
    !info <book> -> Give some informations on the books you typed\n\
    !add <book> -> Add the books you typed to your favorite list\n\
    !fav -> Display your favorite books list\n\
    !clear -> Clear your favorite books list\n\
    !recommendation -> Recommend you 10 books that you might like depending your favorite list\n\
    !del <n>-> Delete n last messages  \n\
    !test -> Simple test that return your name '


responses={
    'greet':'Hello! How are you? Type "help" if you need help', 
    'help':'If it can help you, here are my commands :\n'+help_text,    
    'info':'The only information i have is the list of my commands :\n'+help_text,
    'thank':'You are welcome',
    'thanks':'You are welcome',
    'fallback':'I dont quite understand. Could you repeat that, or type "help".',
}

# global var
FavoriteBooksList = {}

@client.event
async def on_ready():
    print(f'{client.user.name} has connected to Discord!')

@client.event
async def on_member_join(member):
    await member.create_dm()
    await member.dm_channel.send(
        f'Hi {member.name}, welcome to my Discord server!'
    )

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    global FavoriteBooksList
    global temporaryBook

    if message.content[0:5] == '!info':
        response = wikipedia.summary(message.content[6:], sentences=3)

    elif message.content[0:4] == '!add':
        closeBook = closestBook(message.content[5:])
        if closeBook[1]>95:
            if message.author.name in FavoriteBooksList:
                if closeBook[0] not in FavoriteBooksList[message.author.name]:
                    FavoriteBooksList[message.author.name].append(closeBook[0])
            else :
                FavoriteBooksList[message.author.name]=[closeBook[0]]
            response = "The book '"+closeBook[0]+"' was added to your favorite list"
        else:
            temporaryBook = closeBook[0]
            response = "I am not sure that I have this book in my model, the closest book is : '"+closeBook[0]+"', If you want to add it to your list type '!yes' or try another book"

    elif message.content[0:4] == '!fav':
        if message.author.name in FavoriteBooksList:
            response = 'This is your favorite list of books : \n'
            for book in FavoriteBooksList[message.author.name]:
                response = response+book+', '
            if len(FavoriteBooksList[message.author.name]) == 0:
                response = "Your favorite list is empty (use '!add <book>')"
        else:
            response = "Your favorite list is empty (use '!add <book>')"

    elif message.content[0:6] == '!clear':
        if message.author.name in FavoriteBooksList:
            FavoriteBooksList[message.author.name]=[]
        response = "your favorites list has been successfully emptied"

    elif message.content[0:4] == '!yes':
        if message.author.name in FavoriteBooksList:
            if temporaryBook not in FavoriteBooksList[message.author.name]:
                FavoriteBooksList[message.author.name].append(temporaryBook)
        else :
             FavoriteBooksList[message.author.name]=[temporaryBook]
        response = "The book '"+temporaryBook+"' was added to your favorite list"

    elif message.content[0:15] == '!recommendation':
        if message.author.name in FavoriteBooksList:
            if len(FavoriteBooksList[message.author.name])>0:
                myRec = recommendBook(FavoriteBooksList[message.author.name])
                if len(myRec)<5:
                    response = 'Sorry but I do not have enough information about you to suggest books to you, try adding more popular books to your favorite list'
                else:
                    response = 'Thanks to your favorite list, I offer you books that you might like: \n'
                    i = 0
                    for book in myRec:
                        i += 1
                        response = response + str(i) + ". " + book + "\n"

            else :
                response = "First you have to add books to your favorite list (use '!add <books>')"
        else:
            response = "First you have to add books to your favorite list (use '!add <books>')"

    elif message.content[0:4] == '!del':
        nb= int(message.content.split()[1])
        messages = await message.channel.history(limit= nb+1).flatten()
        for each_msg in messages:
            await each_msg.delete()

    elif message.content[0:5] == '!test':
        response = str(message.author.name)

    else:
        user_input = message.content.lower()
        matched_intent = None 
        for intent,pattern in keywords_dict.items():
            if re.search(pattern, user_input): 
                matched_intent=intent  
        key='fallback' 
        if matched_intent in responses:

            key = matched_intent 

        response = responses[key]


    await message.channel.send(response)

client.run(TOKEN)