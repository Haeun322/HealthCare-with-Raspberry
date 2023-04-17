import json #json import
from flask import Flask, render_template, url_for, redirect #flask import
import RPi.GPIO as GPIO #GPIO import
import time #time 모듈 import
import spidev # spidev import
from lcd import drivers #LCD driver improt

mode = 0
dataArr = [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]
strArr = [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]
all_avrHB = 0
all_avrST = 0
cnt = 0
status = False

print("HI") # 작동 테스트

display = drivers.Lcd() #LCD 디스플레이를 받음

print("hello")

spi = spidev.SpiDev() #Spi 통신 설정
spi.open(0,0)
spi.max_speed_hz = 100000 #spi 통신 속도 설정

HEART_PIN = 17 # 하트 모드를 결정하는 버튼 
STRESS_PIN = 27 # 스트레스 및 행복지수 측정 모드를 결정하는 버튼 
SLEEP_PIN = 22 # 수면 점수 계산 모드를 결정하는 버튼 
OUT_PIN = 4 # 메인 화면으로 돌아가는 버튼

LED_PIN1 = 5
LED_PIN2 = 6
LED_PIN3 = 13
LED_PIN4 = 19
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN1,GPIO.OUT)
GPIO.setup(LED_PIN2,GPIO.OUT)
GPIO.setup(LED_PIN3,GPIO.OUT)
GPIO.setup(LED_PIN4,GPIO.OUT)
GPIO.setup(HEART_PIN,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(STRESS_PIN,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(SLEEP_PIN,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(OUT_PIN,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
mode = 0

display.lcd_display_string("test lcd!",1)
print("start program successfully!!")
GPIO.output(LED_PIN4,1)

app = Flask(__name__)
    
@app.route("/") # IP:포트/ 접속 시 IP:포트/main 으로 이동(관리 편하게 하려고)
def p():
    return redirect(url_for('main'))

@app.route("/main")
def main():

    global all_avrHB
    global all_avrST
    global cnt
    global status
    global mode
    global dataArr
    global strArr

    for i in range(14):
        dataArr[i] = -1
        strArr[i] = -1
    all_avrHB = 0
    all_avrST = 0
    cnt = 0
    status = False
    mode = 0
    # 67 ~ 74 기본 세팅 초기화

    return render_template("main.html")

@app.route("/mode")
def mainPage():
    global mode
    input1 = GPIO.input(HEART_PIN) 
    input2 = GPIO.input(STRESS_PIN)
    input3 = GPIO.input(SLEEP_PIN)
    input4 = GPIO.input(OUT_PIN)
    if input1 == 1: # 모드를 심박수 측정 모드로 바꿈
        mode = 1
    elif input2 == 1: # 모드를 스트레스 및 심박수 측정 모드로 바꿈
        mode = 2 
    elif input3 == 1: # 모드를 수면지수 측정 모드로 바꿈
        mode = 3
    elif input4 == 1 and not mode == 0: # 현재 진행 중인 작업을 강제 종료 하고 메인 화면으로 돌아감
        mode = 0
        print("home")
    if mode == 1:
        #print("heart mode")
        GPIO.output(LED_PIN4,0)
        GPIO.output(LED_PIN1,1)
        display.lcd_display_string("Heart Mode ",1) #lcd에 해당 모드 출력
        # heart_mode()
        # mode = 0
    elif mode == 2:
        #print("stress mode")
        GPIO.output(LED_PIN4,0)
        GPIO.output(LED_PIN2,1)
        display.lcd_display_string("Stress Mode ",1)#lcd에 해당 모드 출력
        # stress_mode()
        # mode = 0
    elif mode == 3:
        #print("sleep mode")
        GPIO.output(LED_PIN4,0)
        GPIO.output(LED_PIN3,1)
        display.lcd_display_string("Sleep Mode ",1)#lcd에 해당 모드 출력
        # sleep_mode()
        # mode = 0
    elif mode == 0:
        display.lcd_display_string("Device Home",1)#lcd에 해당 모드 출력
        GPIO.output(LED_PIN4,1)
        GPIO.output(LED_PIN3,0)
        GPIO.output(LED_PIN2,0)
        GPIO.output(LED_PIN1,0)

    return json.dumps({ "mode" : mode })

@app.route("/heart")
def render_heart():
    return render_template("heart.html")

@app.route("/stress")
def render_heart2():
    return render_template("heart.html")

@app.route("/sleep")
def render_heart3():
    return render_template("heart.html")

@app.route("/get_heart")
def heart():
    global cnt
    global all_avrHB
    global all_avrST
    if mode == 1: # 
        getHeartbeat()
        count = getAvr(cnt)
        cnt = count
        return json.dumps({ "data_arr" : dataArr, "now_heartRate" : dataArr[13], "all_avr" : round(all_avrHB/cnt, 1), "mode" : mode })
    elif mode == 2:
        heart, stress = stress_mode()
        for i in range(13):
            dataArr[i] = dataArr[i+1]
        dataArr[13] = heart
        for i in range(13):
            strArr[i] = strArr[i+1]
        strArr[13] = stress
        cnt = cnt + 1
        all_avrST = all_avrST + stress
        return json.dumps({ "data_arr" : dataArr, "now_gap" : strArr[13], "avr_gap" : round(all_avrST/cnt, 1), "mode" : mode })
    elif mode == 3:
        heart, s = sleep_mode()
        for i in range(13):
            dataArr[i] = dataArr[i+1]
        dataArr[13] = heart
        if s == 0:
            return json.dumps({ "data_arr" : dataArr, "all_avr" : round(all_avrHB/cnt, 1), "avr_gap" : round(all_avrST/cnt, 1), "status" : status, "mode" : mode })
        elif s == 1:
            return json.dumps({ "data_arr" : dataArr, "all_avr" : round(all_avrHB/cnt, 1), "avr_gap" : round(all_avrST/cnt, 1), "status" : status, "mode" : mode })
        elif s == -1:
            return json.dumps({ "data_arr" : dataArr, "all_avr" : round(all_avrHB/cnt, 1), "avr_gap" : round(all_avrST/cnt, 1), "status" : "END", "mode" : mode })

@app.route("/resault/<m>")
def devRes(m):
    m = m
    return render_template("resault.html")

@app.route("/get_res")
def sendRes():
    global all_avrHB
    global all_avrST
    global cnt
    global mode

    if cnt == 0: return json.dumps({ "mode" : mode })

    if mode == 1:
        return json.dumps({ "resHB" : round(all_avrHB/cnt, 2), "mode" : mode })
    elif mode == 2:
        return json.dumps({ "resST" : round(all_avrST/cnt, 2), "mode" : mode })
    elif mode == 3:
        return json.dumps({ "resHB" : round(all_avrHB/cnt, 2), "count" : cnt, "mode" : mode })
    else:
        return json.dumps({ "mode" : mode })

def analog_read(channel):
    ret = spi.xfer2([1, (8 + channel) << 4,0])
    adc_out = ((ret[1] & 3) << 8) + ret[2]
    return adc_out

def heart_mode(): # 심박수 측정 기능 함수
    sum=0
    if not mode == 0:
        for i in range(10):
            reading = analog_read(0)
            heart = reading/10
            #print("heart : %d"% heart)
            sum += heart
            time.sleep(0.05)
        sum/=10
        print("average : %d"%sum)
        return round(sum, 2)

def stress_mode(): # 스트레스 지수 및 행복 지수 측정 기능 함수
    stress = 0
    if not mode == 0:
        a = []
        sum = 0
        for i in range(10):
            reading = analog_read(0)
            heart = reading/10
            #print("heart : %d"% heart)
            a.append(heart)
            sum += heart
            time.sleep(0.05)
        for i in range(1,10):
            stress += a[i]-a[i-1] #심박수 값을 리스트에 넣은 후 변화량 계산
        if stress < 0:
            stress = stress * -1
        #print("stress : %d"%stress)
        if stress < 10:
            print("your stress is low")
        elif stress >= 10 and stress <= 15:
            print("your stress is middle")
        else:
            print("your stress is high")
        return round(sum/10, 2), round(stress, 2)

def sleep_mode(): # 수면 점수 계산 기능 함수
    if not mode == 0:
        global status
        h = round(heart_mode(), 2)
        if not status:
            if h <= 50:
                status = True
                return h, 1
            return h, 0
        else:
            if h <= 50: return h, 1
            else:
                status = False
                return h, -1 

def getHeartbeat(): # 심장박동수 측정해서 dataArr에 넣음
    HB = heart_mode()
    # 심장 박동수 측정, HB에 대입

    for i in range(13):
        dataArr[i] = dataArr[i+1]
    dataArr[13] = HB

def getAvr(cnt):
    global all_avrHB
    count = cnt + 1

    all_avrHB = all_avrHB + dataArr[13]

    return count
        
if __name__ == "__main__":
    app.run(host="0.0.0.0",port=5000)