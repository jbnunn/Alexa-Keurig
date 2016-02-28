#!/usr/bin/python3

# required libraries
import sys
import ssl
import paho.mqtt.client as mqtt
import time
import json
import RPi.GPIO as GPIO

def main():
    mqttc = mqtt.Client(client_id="RPi")

    mqttc.on_connect = on_connect
    mqttc.on_message = on_message
    mqttc.on_subscribe = on_subscribe

    mqttc.tls_set("./certs/rootCA.pem",
                  certfile="./certs/cert.pem",
                  keyfile="./certs/privateKey.pem",
                  tls_version=ssl.PROTOCOL_TLSv1_2,
                  ciphers=None)

    mqttc.connect("<your-endpoint-here>.iot.us-east-1.amazonaws.com", port=8883)
    print("Connect is done")
    mqttc.loop_forever()


# called while client tries to establish connection with the server
def on_connect(mqttc, obj, flags, rc):

    if rc == 0:
        print ("Subscriber Connection status code: " +
               str(rc) + " | Connection status: successful")
    elif rc == 1:
        print ("Subscriber Connection status code: " + str(rc) +
               " | Connection status: Connection refused")

    mqttc.subscribe("$aws/things/coffee/shadow/update/accepted", 1)

# called when a topic is successfully subscribed to
def on_subscribe(mqttc, obj, mid, granted_qos):
    print("Subscribed: " + str(mid) + " " +
          str(granted_qos) + "data" + str(obj))

# called when a message is received by a topic
def on_message(mqttc, obj, msg):
    print("Received message from topic: " + msg.topic)
    print(str(msg.payload))
    thingdata = json.loads(str(msg.payload))

    if 'desired' in thingdata['state']:
        brewstate = thingdata['state']['desired']['brew'].lower()

        if brewstate == "on" or brewstate == "brew" or brewstate == "start":
            print("Will brew!")
            payload = '{"state" : { "reported" : { "brew" : "on" } } }'
            mqttc.publish("$aws/things/coffee/shadow/update", payload)
	    start_brew()
        elif brewstate == "off" or brewstate == "stop":
            print("Stoping brew!")
            payload = '{"state" : { "reported" : { "brew" : "off" } } }'
            mqttc.publish("$aws/things/coffee/shadow/update", payload)
            stop_brew()
        else:
            print("Invalid state")
            payload = '{"state" : { "reported" : { "brew" : "off" } } }'
            mqttc.publish("$aws/things/coffee/shadow/update/rejected", payload)
            stop_brew()

def start_brew():
    p.start(7.5)
    GPIO.output(LIGHTPIN, GPIO.HIGH)

    p.ChangeDutyCycle(9.3)
    time.sleep(.5)
    p.ChangeDutyCycle(8.0)
    time.sleep(1)

    stop_brew()

def stop_brew():
    GPIO.output(LIGHTPIN, GPIO.LOW)

if __name__ == '__main__':
    SERVOPIN = 18
    LIGHTPIN = 12

    GPIO.setmode(GPIO.BOARD)
    GPIO.setwarnings(False)

    GPIO.setup(SERVOPIN, GPIO.OUT)
    GPIO.setup(LIGHTPIN, GPIO.OUT)

    p = GPIO.PWM(SERVOPIN, 50)
    p.ChangeDutyCycle(9.3)

    try:
        main()
    except KeyboardInterrupt:
        p.stop()
        GPIO.cleanup()
        sys.exit()
