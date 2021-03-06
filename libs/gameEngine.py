import random
import requests
import operator
import json
from flask import session 
from datetime import datetime as dt
import base64
base_url = "http://www.jservice.io/api/"

def startGame(names):
    rCategories = initRound(session['round'])
    session['categories'] = rCategories
    players = [{'number':1, 'name':names[0], 'score':0, 'date':dt.date(dt.today()).isoformat()}]
    if len(names) > 1:
        players.append({'number':2, 'name':names[1], 'score':0, 'date':dt.date(dt.today()).isoformat()})
    if len(names) > 2:
        players.append({'number':3, 'name':names[2], 'score':0, 'date':dt.date(dt.today()).isoformat()})
    session['players'] = players    
    session['currentPlayer'] = 1

def initRound(rNumber):
    categoriesFull = getRandomCategories()
    rCategories = []
    while len(rCategories) <= 5:
        category = fetchCategory(categoriesFull, rNumber)
        # make sure no repetition
        if not any(category['title'] == c['title'] for c in rCategories):
            rCategories.append(category)
    return rCategories

def getRandomCategories():
    offset = random.randint(1, 183)*100
    print(offset)
    response = requests.get(base_url+"categories?count=100&offset="+str(offset))
    return response.json()

def fetchCategory(categories, round):
    rClues = []
    while len(rClues) < 5:
        rClues = []
        index = random.randint(0,99)
        categoryId = categories[index]['id']
        response = requests.get(base_url+"category?id="+str(categoryId))
        category = response.json()
        categoryTitle = category['title']

        clues = category['clues'] #-->list of dicts
        random.shuffle(clues)
        
        rValues = [200,400,600,800,1000]

        rClues = clueValidator(clues, rValues, rClues)
        print(len(rClues))
    rClues.sort(key=operator.itemgetter('value'), reverse=True)
    
    rCategory = {'title':categoryTitle, 'clues':rClues} 
        
    return rCategory

# receives list of clues and round-values and empty list of clues for the round
# returns list of all the valid clues matching the values from the round-values list (one for each value)
def clueValidator(clues, rValues, rClues):
    for clue in clues:
        for index, val in enumerate(rValues):
            newGameDate = dt.strptime("2001-11-01T12:00:00.000Z", "%Y-%m-%dT%H:%M:%S.%fZ")
            airdate = dt.strptime(clue['airdate'], "%Y-%m-%dT%H:%M:%S.%fZ")
            if airdate > newGameDate:
                if clue['value'] == val:
                    if clue['answer'] is not None and clue['question'] is not None:
                        #base64 encode answers so they dont show in dev tools
                        string = clue['answer']
                        encodedStr = base64.b64encode(string.encode())
                        clue['answer'] = encodedStr
                        if session['round'] == 2:
                            clue['value']*=2
                        rClues.append(clue)
                        rValues.remove(val)
                        break
    return rClues

def createNewRound(rNumber):
    rCategories = initRound(rNumber)
    session['categories'] = rCategories
    session['currentPlayer'] = 1

def checkAnswer(clueAnswer, pAnswer):
    #automatically return false(incorrect answer) if user enters empty string or space
    if pAnswer == '' or pAnswer == ' ':
        return False
    #remove single quotes and first char 'b' which were added during encoding process
    clueAnswer = clueAnswer.replace("'","")
    clueAnswer = clueAnswer[1:]
    #decode correct answer
    decodedClueAnswer = base64.b64decode(clueAnswer)
    decodedClueAnswer = decodedClueAnswer.decode('ascii')
    #convert all to lowercase
    decodedClueAnswer = decodedClueAnswer.lower()
    pAnswer = pAnswer.lower()
    #see if user gave correct answer in their response
    result = decodedClueAnswer.find(pAnswer)
    if result == -1:
        return False
    else:
        return True

def updateScore(value, currentPlayer, result):
    for p in session['players']:
        if p['number'] == currentPlayer:
            if result == True:
                p['score'] += int(value)
                session.modified = True
            else:
                p['score'] -= int(value)
                session.modified = True
    if session['currentPlayer'] < len(session['players']):
        session['currentPlayer'] += 1
    else:
        session['currentPlayer'] = 1

def disableClue(clueId):
    if 'disabled' not in session:
        session['disabled']=[int(clueId)]
        session.modified = True
    else: 
        session['disabled'].append(int(clueId))
        session.modified = True

def getLeader():
    leader = max(session['players'], key=lambda x: x['score'])
    return leader

def updateLeaderBoard():
    with open('leaderBoard.json') as read_file:
        st = read_file.read()
        read_file.seek(0)
        #on first game the file will contain just an empty string
        if st != ' ': #on all subsequent games
            data = json.load(read_file)
            for p in session['players']: 
                data.append(p)
        else:#on first game
            data = session['players']
    
    #sort data according to score descending
    data.sort(key=operator.itemgetter('score'), reverse=True)
    #remove lowest scores so that only 10 remain at most
    if len(data)>10:
        n = len(data)-10
        data = data[:-n]

    with open('leaderBoard.json', 'w+') as write_file:
        json.dump(data, write_file)

def getLeaderBoard():
    with open('leaderBoard.json') as read_file:
        st = read_file.read()
        read_file.seek(0)
        if st == ' ':
            leaderBoard = []
            return leaderBoard
        leaderBoard = json.load(read_file)
    return leaderBoard




