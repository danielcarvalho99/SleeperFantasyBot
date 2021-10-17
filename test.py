import requests
import telegram
import logging
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('API_KEY')

from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext, Filters
from telegram.update import Update

# PATHS
GET_USER = 'https://api.sleeper.app/v1/user/'
GET_PLAYERS = "https://api.sleeper.app/v1/players/nfl"
LEAGUES = '/leagues/nfl/2021'
LEAGUE_ID = "https://api.sleeper.app/v1/league/"

# MESSAGES
START_MESSAGE = "Olá, esse é o SleeperFantasyBot! Digite /find para buscar em quais ligas o jogador que você deseja está disponível"
FIND_PLAYER_MESSAGE = "Informe o nome do seu usuário seguido dos dois nomes do jogador que deseja procurar. Ex: usuario_1 Tom Brady"
HELP_MESSAGE = "Digite /start para visualizar a mensagem inicial e /find para buscar a disponibilidade de um jogador nas suas ligas."

def find_user_id(username):
    url = (GET_USER + username).strip()

    response = requests.get(url).json()
    return response['user_id']

def find_user_leagues(id):
    leagues = []
    url = (GET_USER + id + LEAGUES).strip()
    response = requests.get(url).json()

    for league in response:
        leagues.append((league['name'], league['league_id']))

    return leagues

def show_results(update, context, avaliable):
    if(len(avaliable) == 0):
        update.message.reply_text('O jogador não está disponível em nenhuma liga!')
        return

    elif(len(avaliable) == 1):
        update.message.reply_text('O jogador está disponível na seguinte liga:')
        update.message.reply_text(avaliable[0])
    else:
        update.message.reply_text(f'O jogador está disponível em {len(avaliable)} ligas:')
        for league in avaliable:
            update.message.reply_text(league)


def is_avaliable_in_league(league, index, player_key, avaliable, not_avaliable):
    
    if(player_key == "ERROR"):
        return
    
    url = (LEAGUE_ID + league[index][1] + '/rosters').strip()
    response = requests.get(url).json()
    
    for rosters in response:
        players = rosters['players']
        if player_key in players:
            not_avaliable.append(league[index][0])
            return

    avaliable.append(league[index][0])

def is_available_in_all_leagues(leagues, player_key):
    avaliable =[]
    not_avaliable = []
    
    for i in range(0, len(leagues)):
        is_avaliable_in_league(leagues, i, player_key, avaliable, not_avaliable)

    return avaliable

def find_player_key(player_name):
    url = GET_PLAYERS
    response = requests.get(url).json()
    values = list(response.values())

    i = 0

    for key in response.keys():
        name = values[i]['first_name'] + ' ' + values[i]['last_name']
        if(name == player_name):
            return key
        
        i = i + 1
    
    print('Player does not exist!')
    return "ERROR"

# Bot Commands
def start(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, 
    text=START_MESSAGE)

def help(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, 
    text=START_MESSAGE)

def find(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, 
    text=FIND_PLAYER_MESSAGE)

def search(update: Update, context: CallbackContext):
    values = update.message.text.split()
    username = values[0]
    player_name = values[1] + ' ' + values[2]

    context.bot.send_message(chat_id=update.effective_chat.id, text="Buscando por " + player_name + "...")

    id = find_user_id(username)
    leagues = find_user_leagues(id)

    key = find_player_key(player_name)
    avaliables = is_available_in_all_leagues(leagues, key)
    show_results(update, context, avaliables)

def main(token):
    bot = telegram.Bot(token)
    updater = Updater(token, use_context=True)
    
    dispatcher = updater.dispatcher
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)

    # Handlers
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('help', help))
    dispatcher.add_handler(CommandHandler('find', find))
    dispatcher.add_handler(MessageHandler(Filters.text & (~Filters.command), search))

    updater.start_polling()

# main
if __name__ == "__main__":
    main(TOKEN)