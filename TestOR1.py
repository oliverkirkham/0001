from cgi import print_arguments, test
from random import randint, random
from time import sleep
import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt
import threading
import os


broker="127.0.0.1"
port=1883 #broker port (default is 1883)
GudeID="OR1" #ID of the controlled gude
ShutdownTopic="com/jonesav/androidscreen/shutdown"
GudePowerTopic="com/jonesav/androidscreen/shutdown/confirm"
GUDEcommandtopic="com/jonesav/secretbox/{}/cmd/cli".format(GudeID)
shutdowndelay=60 #delay in seconds between shutdown command received and power off sent
powerstate=2 #powerstate of the GUDE
refresh = 5 #refresh rate of the data on the android screen (in seconds per frame) anything lower than 5 causes weird behavior
KwH = 1.5 #power consumption of the OR
powersaved= 0
co2multi= 0.193 #co2 generated per KwH
cpkwh= 0.34 #Cost per KwH


def on_connect(client, userdata, flags, rc): #on connecting to broker print error code
    client.subscribe(ShutdownTopic)
    print("Connected with result code "+str(rc))
    return
    



def on_messageshutdown(client, userdata, msg,): #on shutdown message confirm recived then wait 60 s
    global powerstate
    decodedmessage = msg.payload.decode('UTF-8')
    print("Command Received:", decodedmessage, "Preparing to Shutdown")
    msgs = [{'topic':GudePowerTopic, 'payload':'AZ5'}]
    publish.multiple(msgs, hostname=broker)
    print("shutdown confirm sent")
    sleep(shutdowndelay)
    print("powering off")
    msgs = [{'topic':GUDEcommandtopic, 'payload':'port all set 2'}] #after 60 seconds shut the GUDE down
    publish.multiple(msgs, hostname=broker)
    powerstate = (0) #set powerstate to 0 and shutdown before triggering other threads
    print(powerstate)
    subpoweron.start()
    savingscalc.start()
    return

def on_messagepoweron(client, userdata, msg): #on reciving power on message
    global powerstate
    wow = msg.payload.decode('UTF-8')
    if wow == "port all set 1":
        powerstate = (1)
        msgs = [{'topic':"com/jonesav/androidscreen/data/kwh", 'payload':round(0, 2)},
        ("com/jonesav/androidscreen/data/co2", round(0, 2), 0, False),
        ("com/jonesav/androidscreen/data/money", round(0, 2), 0, False)]
        publish.multiple(msgs, hostname=broker)
        print("message received powering on:", wow, powerstate)
        client.unsubscribe(GUDEcommandtopic)
        print("resetting")
        os.system("python TestOR1.py")
        exit()
    else :
        print("incorred command", wow)
        subscribingpoweron()


def powersavingscalc(powersaved): #power savings calculation
    global powerstate
    while powerstate == 0:
        powersaved=(powersaved)
        co2saved=(powersaved*co2multi)
        moneysaved=(powersaved*cpkwh)
        print("powersaved", round(powersaved, 3), "Co2 Saved", round(co2saved, 3), "Money Saved", round(moneysaved, 3))
        msgs = [{'topic':"com/jonesav/androidscreen/data/kwh", 'payload':round(powersaved, 2)},
        ("com/jonesav/androidscreen/data/co2", round(co2saved, 2), 0, False),
        ("com/jonesav/androidscreen/data/money", round(moneysaved, 2), 0, False)]
        publish.multiple(msgs, hostname=broker)
        powersaved=(powersaved+(KwH/(3600/refresh)))
        sleep(refresh)
    else:
        return



client = mqtt.Client() #mqtt config stuff
client.connect(broker, port, 60)
client.on_connect = on_connect


#configuring mqtt subscriptions
def subscribingshutdown():
    client.on_message = on_messageshutdown
    client.loop_forever()

def subscribingpoweron():
    client.unsubscribe(ShutdownTopic)
    client.subscribe(GUDEcommandtopic)
    client.on_message = on_messagepoweron



#starting theads
try:
    subshutdown = threading.Thread(target=subscribingshutdown)
    subpoweron = threading.Thread(target=subscribingpoweron)
    savingscalc = threading.Thread(target=powersavingscalc, args=[powersaved])
    subshutdown.start()
except:
    print("error starting threads")
while 1:
    pass
print("hmm seems we're out of ones and zeros")
