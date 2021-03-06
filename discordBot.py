#!/usr/bin/env python3

import discord
import asyncio
import ujson as json
import requests
import time
import configparser
from operator import itemgetter


Config = configparser.ConfigParser()
Config.read("discordBot.ini")
token = Config.get("tokens","token")

def submissionSearch(query):
    """Simple Elasticsearch Query"""
    headers={'Accept': 'application/json', 'Content-type': 'application/json'}
    uri = "http://localhost:9200/rs_deltab/submissions/_search"
    query = json.dumps({"query":{"bool":{"filter":[{"range":{"num_comments":{"gte":50}}}],"must":{"multi_match":{"fields":["selftext","title"],"query": query}}}},"size":5})
    response = requests.get(uri, data=query, headers=headers)
    response = json.loads(response.text)
    print (str(response))
    responses = []
    for hit in response["hits"]["hits"]:
        responses.append(hit["_source"])
    responses.sort(key=lambda x: (int(x['score'])), reverse=True)
    result = ""
    for hit in responses:
        result += "https://www.reddit.com" + hit['permalink'] + "\n"
    return result

def search(query):
    """Simple Elasticsearch Query"""
    headers={'Accept': 'application/json', 'Content-type': 'application/json'}
    uri = "http://localhost:9200/rs/submissions/_search"
    response = requests.get(uri, data=query, headers=headers)
    results = json.loads(response.text)
    return results

def answerQuestion(query):
    """Simple Elasticsearch Query"""
    headers={'Accept': 'application/json', 'Content-type': 'application/json'}
    uri = "http://localhost:9200/rs/submissions/_search"
    query = json.dumps({
        "query": {
            "match": {
                "_all": query
            }
        }, "size" : 200
    })
    response = requests.get(uri, data=query, headers=headers)
    response = json.loads(response.text)
    responses = []
    for hit in response["hits"]["hits"]:
        responses.append(hit["_source"])
    responses.sort(key=lambda x: (int(x['score'])), reverse=True)
    for hit in responses:
        source = hit
        if 'selftext' in source and source['selftext'] is not None:
            if source['selftext'] == "[removed]" or source['selftext'] == "[deleted]": continue
            if len(source["selftext"]) > 2 and len(source["selftext"]) < 250:
                answer = source["selftext"]
                score = source["score"]
                result = "[score: " + str(score) + " subreddit: " + str(source['subreddit']) + "] " + answer
                return result

client = discord.Client()

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

@client.event
async def on_message(message):
    print(message.content)
    print(message.author)
    print(message.channel)
    if str(message.author).find(client.user.name) and str(message.channel).lower() == "discord_integration_testing":
        if message.content.startswith('!test'):
            counter = 0
            tmp = await client.send_message(message.channel, 'Calculating messages...')
            async for log in client.logs_from(message.channel, limit=100):
                if log.author == message.author:
                    counter += 1

            await client.edit_message(tmp, 'You have {} messages.'.format(counter))
        elif message.content.startswith('!sleep'):
            await asyncio.sleep(5)
            await client.send_message(message.channel, 'Done sleeping')
        elif message.content.startswith('!pushshift analyze user'):
            author = str(message.content).split()[-1]
            await client.send_message(message.channel, author)
        elif message.content.startswith('!pushshift submission search'):
            query = str(message.content)[29:]
            response = submissionSearch(query)
            await client.send_message(message.channel, response)
        elif message.content.startswith('!pushshift elasticsearch'):
            es_string = str(message.content)[25:]
            results = json.dumps(search(es_string))
            if len(results) < 2000:
                await client.send_message(message.channel, results)
            else:
                await client.send_message(message.channel, "The response from Elasticsearch is too large to put here. (This will be fixed soon -- jmb)")
        elif message.content.startswith('!pushshift what is the current epoch'):
                await client.send_message(message.channel, str(int(time.time())))
        else:
                response = answerQuestion(str(message.content))
                await client.send_message(message.channel, response)

client.run(token)
