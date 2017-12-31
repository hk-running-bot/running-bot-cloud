from .bot import bot
import skygear
import os

@skygear.handler('telegam_hook', method=['POST'])
def handle_post(request):
    b = request.stream.read()
    s = b.decode(request.charset, request.encoding_errors)
    update = telebot.types.Update.de_json(s)
    bot.process_new_messages([update.message])
    return {'processed': 'yes'}

@skygear.handler('hello', method=['GET'])
def handle_get(request):
    print("Hello")
    hostname = os.environ.get('HOSTNAME', 'NA')
    return {'message': 'Hello', 'hostname': hostname}

print(os.environ)

def start_polling():
    print("called")
    bot.polling(none_stop=False, interval=0, timeout=20)

if os.environ["HOSTNAME"].startswith("hkrunningbot"):
    print("now start polling")
    import subprocess
    os.system('python3 -V')
    subprocess.Popen(['python3', '-m', 'bot'])
    print("started")
else:
    print("should not start.")
