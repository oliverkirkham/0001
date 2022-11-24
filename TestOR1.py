from cgi import print_arguments, test
from random import randint, random
from time import sleep
import paho.mqtt.publish as publish
import paho.mqtt.client as mqtt
import threading
import os


broker="192.168.11.47"
port=1883 #broker port (default is 1883)
GudeID="OR1" #ID of the controlled gude
ShutdownTopic="com/jonesav/androidscreen/shutdown"
GudePowerTopic="com/jonesav/androidscreen/shutdown/confirm"
PowerOnTopic="jonesav/secretbox/{}/cmd/cli".format(GudeID)
PowerOffTopic="jonesav/secretbox/{}/cmd/cli".format(GudeID)
shutdowndelay=60 #delay in seconds between shutdown command received and power off sent
powerstate=2
refresh = 5
KwH = 1.5
powersaved= 0.1
co2multi= 0.193
cpkwh= 0.34


def on_connect(client, userdata, flags, rc): #on connecting to broker print error code
    client.subscribe(ShutdownTopic)
    print("Connected with result code "+str(rc))
    return
    



def on_messageshutdown(client, userdata, msg,): #on shutdown message confirm recived then wait 60 s
    global powerstate
    wow = msg.payload.decode('UTF-8')
    print("Command Received:", wow, "Preparing to Shutdown")
    msgs = [{'topic':GudePowerTopic, 'payload':'AZ5'}]
    publish.multiple(msgs, hostname=broker)
    print("shutdown confirm sent")
    sleep(shutdowndelay)
    print("powering off")
    msgs = [{'topic':PowerOffTopic, 'payload':'port all set 2'}] #after 60 seconds shut the GUDE down
    publish.multiple(msgs, hostname=broker)
    powerstate = (0) #set powerstate to 0 and shutdown before triggering other threads
    print(powerstate)
    subpoweron.start()
    savingscalc.start()
    return

def on_messagepoweron(client, userdata, msg): #on reciving power on message
    global powerstate
    wow = msg.payload.decode('UTF-8')
    powerstate = (1)
    print("message received powering on:", wow, powerstate)
    client.unsubscribe(PowerOnTopic)
    os.system("python TestOR1.py")
    print("resetting")
    exit()


def powersavingscalc(powersaved): #power savings calculation
    global powerstate
    while powerstate == 0:
        powersaved=(powersaved)
        co2saved=(powersaved*co2multi)
        moneysaved=(powersaved*cpkwh)
        print("powersaved", round(powersaved, 3), "Co2 Saved", round(co2saved, 3), "Money Saved", round(moneysaved, 3))
        msgs = [{'topic':"OliverK/test/kwh", 'payload':round(powersaved, 2)},
        ("OliverK/test/co2", round(co2saved, 2), 0, False),
        ("OliverK/test/money", round(moneysaved, 2), 0, False)]
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
    client.subscribe(PowerOnTopic)
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
