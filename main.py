#!/usr/bin/env python3

"""
Cozmo.AI
v. 0.4.9
Extending Anki Cozmo robot's abilities, by adding human voice recognition, basic AI bot functions and special commands
like checking the time/weather, playing music on PC connected speaker etc.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
"""

try:
    import asyncio
    import os
    import sys
    import glob
    import json
    import time
    import datetime
    import random
    import requests
    import speech_recognition as sr
    import cozmo

except ImportError:
    sys.exit("Some packages are required. Do `pip3 install cozmo requests "
             "termcolor SpeechRecognition Pillow PyAudio` to install.")

from cozmo.util import degrees, distance_mm, speed_mmps
from datetime import datetime as dtm
from termcolor import cprint
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from random import randint
from requests import get

# General Parameters
version = "ver. 0.4.9"
title = "Cozmo.AI       " + version
author = "By c64-dev (nikosl@protonmail.com)"
descr = "Adding AI chat and voice command functionality to Cozmo robot."
base_url = "https://api.darksky.net/forecast/"
ip_url = "http://ipinfo.io/json"
api_key = "9673b21b3567a2e9d1009b00908453c5/"
parms = "?units=si"

# Special Commands
name = ["Cozmo", "Cosmo", "cosmo", "cozmo", "osmo", "Kuzma", "kuzma", "Prisma", "Goodwill", "Robert", "robot",
        "Christmas", "customer", "cuz my", "cuz", "Kosmos", "kiasma", "Kismet", "Kokomo"]
cmd_exit = ["exit", "bye", "quit"]
# cmd_forward = ["forward", ]
# cmd_backward = ["back", ]
# cmd_right = ["right", ]
# cmd_left = ["left", ]
# cmd_arm = ["lift", "arm"]
# cmd_head = ["look", "up"]
# cmd_follow = ["follow", "face"]
cmd_photo = ["photo", ]  # OK
# cmd_blocks = ["blocks", ]
cmd_dance = ["dance", ]  # OK
# cmd_sleep = ["sleep", ]
# cmd_charge = ["charge", "charger"]
cmd_music_rock = ["rock", ]  # OK
cmd_music_favourites = ["favorite", ]  # OK
cmd_music_stop = ["stop", ]  # OK
cmd_weather_tomorrow = ["weather", "tomorrow"]  # OK
cmd_weather_forecast = ["forecast", ]  # OK
cmd_time = ["time", ]  # OK
cmd_sing = ["sing", ]  # OK
cmd_vol_mute = ["mute", ]  # OK
cmd_vol_min = ["lower", ]  # OK
cmd_vol_mid = ["higher", ]  # OK
cmd_vol_max = ["maximum", ]  # OK
cmd_freeplay = ["freeplay", "free play", "FreePlay"] #OK


# Initialize system
def initCozmo():
    global log, user_name, interval

    cozmo.robot.Robot.drive_off_charger_on_connect = False
    _ = os.system('cls' if os.name == 'nt' else 'clear')
    cprint(title, "green", attrs=['bold'])
    cprint(author, "green")
    print(descr)
    print()
    cprint("Initializing system...", "yellow")
    weather()
    log = initLog()
    interval = 3  # Setting the initial audio polling interval in seconds.
    print("System init ok")
    print("Connected to Cozmo!")
    print()
    printSupportedCommands()
    print()

    # try:
    cozmo.run_program(wake_up)
    cozmo.run_program(freeplay)
    cozmo.run_program(mainLoop)  # ALT: (mainLoop, use_viewer=True, force_viewer_on_top=True)
    sys.exit(0)

    #   ONLY FOR TESTING PURPOSES
    # except SystemExit as e:
    #    print('exception = "%s"' % e)
    #    cprint('\nGoing on without Cozmo: for testing purposes only!', 'red')
    #    mainLoop(None)


# Main Program Loop
def mainLoop(robot):
    global humanString, cozmoString, interval

    # Reset variables and connect to AI bot
    humanString = None
    cozmoString = None
    interval = 5
    pb = AIBot()

    try:
        # Connect to
        pb.browser.get(pb.url)
        robot.say_text("Yes " + user_name + "?", use_cozmo_voice=True, duration_scalar=0.6, voice_pitch=0)\
            .wait_for_completed()
    except:
        pb.browser.close()
        # TODO: Have a more elegant exit to the program.
        sys.exit(0)

    while True:
        # In a loop, listen to user
        try:
            pb.get_form()
        except:
            sys.exit(0)

        if robot:
            flash_backpack(robot, True)
        listen_robot(robot)
        humanString = listen_robot.parsedText

        if robot:
            flash_backpack(robot, False)

        # Here we look for our special commands (quit, time, weather, movements etc).
        # If none are found we move forward with the chatbot and listen again in a loop.
        check_quit()
        check_time(robot)
        check_weather(robot)
        check_music_rock(robot)
        check_music_fav(robot)
        check_music_stop(robot)
        check_dance(robot)
        check_song(robot)
        check_volume(robot)
        check_photo(robot)
        check_freeplay(robot)

        # Else, we log what the human said (optional).
        # addEntry(log, "Human says: " + humanString)
        print("Human says: " + humanString)

        # Get bot's response
        pb.send_input(humanString)
        cozmoString = pb.get_response()

        print("Cozmo says: " + cozmoString)
        # addEntry(log, "Cozmo says: " + cozmoString)

        # Forward to Cozmo.
        robot.say_text(cozmoString, use_cozmo_voice=True, duration_scalar=0.6, voice_pitch=0).wait_for_completed()
        # cozmo.run_program(random_anim(robot))


# Special Commands Init #
def check_quit():
    global humanString
    activate = set(name).intersection(humanString.split())
    command = set(cmd_exit).intersection(humanString.split())
    if activate and command:
        print("Human says: " + humanString)
        # addEntry(log, "Conversation ended.")
        print("")
        cprint("Exit requested by user", "yellow")
        sys.exit(0)
    else:
        return


def check_time(robot):
    global humanString
    activate = set(name).intersection(humanString.split())
    command = set(cmd_time).intersection(humanString.split())
    if activate and command:
        clock(robot)
        listen_robot(robot)
        humanString = listen_robot.parsedText
    else:
        return


def check_weather(robot):
    global humanString
    concString = humanString.replace('weather', '')
    activate = set(name).intersection(humanString.split())
    command01 = set(cmd_weather_tomorrow).intersection(concString.split())
    command02 = set(cmd_weather_forecast).intersection(concString.split())
    if activate:
        if command01:
            print("Human says: " + humanString)
            # addEntry(log, "Human says: " + humanString)
            robot.play_anim("anim_memorymatch_point_player_audio").wait_for_completed()
            #robot.say_text("Gathering weather data...", use_cozmo_voice=True, duration_scalar=0.6,
            # voice_pitch=0).wait_for_completed()
            cprint("Gathering weather data... Please wait.", "yellow")
            weather()
            # addEntry(log, "Cosmo says: " + tomorrow_response)
            robot.say_text(tomorrow_response, use_cozmo_voice=True, duration_scalar=0.6,
                           voice_pitch=0).wait_for_completed()
            print("Cozmo says: " + tomorrow_response)
            listen_robot(robot)
            humanString = listen_robot.parsedText
        elif command02:
            print("Human says: " + humanString)
            # addEntry(log, "Human says: " + humanString)
            cprint("Gathering weather data... Please wait.", "yellow")
            # addEntry(log, "Cosmo says: " + forecast_response)
            robot.say_text(forecast_response, use_cozmo_voice=True, duration_scalar=0.6,
                           voice_pitch=0).wait_for_completed()
            print("Cozmo says: " + forecast_response)
            listen_robot(robot)
            humanString = listen_robot.parsedText
        else:
            return


def check_music_rock(robot):
    global humanString
    activate = set(name).intersection(humanString.split())
    command = set(cmd_music_rock).intersection(humanString.split())
    if activate and command:
        print("Human says: " + humanString)
        # addEntry(log, "Human says: " + humanString)
        print("Cozmo says: Playing rock music.")
        robot.say_text("Playing rock music.", use_cozmo_voice=True, duration_scalar=0.6,
                       voice_pitch=0).wait_for_completed()
        print("* Playing music *")
        os.system("""osascript -e 'tell app "iTunes" to play playlist "Rock"'""")
        partytime(robot)
        freeplay(robot)
        listen_robot(robot)
        humanString = listen_robot.parsedText
    else:
        return


def check_music_fav(robot):
    global humanString
    activate = set(name).intersection(humanString.split())
    command = set(cmd_music_favourites).intersection(humanString.split())
    if activate and command:
        print("Human says: " + humanString)
        # addEntry(log, "Human says: " + humanString)
        print("Cozmo says: Sure thing " + user_name)
        robot.say_text("Sure thing " + user_name, use_cozmo_voice=True, duration_scalar=0.6,
                       voice_pitch=0).wait_for_completed()
        print("* Playing music *")
        os.system("""osascript -e 'tell app "iTunes" to play playlist "90s"'""")
        partytime(robot)
        freeplay(robot)
        listen_robot(robot)
        humanString = listen_robot.parsedText
    else:
        return


def check_music_stop(robot):
    global humanString
    activate = set(name).intersection(humanString.split())
    command = set(cmd_music_stop).intersection(humanString.split())
    if activate and command:
        print("Human says: " + humanString)
        # addEntry(log, "Human says: " + humanString)
        print("Cozmo says: Ok " + user_name)
        robot.say_text("Ok " + user_name, use_cozmo_voice=True, duration_scalar=0.6, voice_pitch=0).wait_for_completed()
        print("* Stopping music *")
        os.system("""osascript -e 'tell app "iTunes" to quit'""")
        listen_robot(robot)
        humanString = listen_robot.parsedText
    else:
        return


def check_dance(robot):
    global humanString
    activate = set(name).intersection(humanString.split())
    command = set(cmd_dance).intersection(humanString.split())
    if activate and command:
        print("Human says: " + humanString)
        # addEntry(log, "Human says: " + humanString)
        print("Cozmo says: No problem " + user_name)
        robot.say_text("No problem " + user_name, use_cozmo_voice=True, duration_scalar=0.6,
                       voice_pitch=0).wait_for_completed()
        print("* Playing music *")
        robot.play_audio(cozmo.audio.AudioEvents.MusicStyle80S1159BpmLoop)
        partytime(robot)
        listen_robot(robot)
        humanString = listen_robot.parsedText
    else:
        return


def check_song(robot):
    global humanString
    activate = set(name).intersection(humanString.split())
    command = set(cmd_sing).intersection(humanString.split())
    if activate and command:
        print("Human says: " + humanString)
        # addEntry(log, "Human says: " + humanString)
        singing(robot)
        listen_robot(robot)
        humanString = listen_robot.parsedText
    else:
        return


def check_volume(robot):
    global humanString
    concString = humanString.replace('volume', '')
    activate = set(name).intersection(humanString.split())
    command01 = set(cmd_vol_mute).intersection(concString.split())
    command02 = set(cmd_vol_min).intersection(concString.split())
    command03 = set(cmd_vol_mid).intersection(concString.split())
    command04 = set(cmd_vol_max).intersection(concString.split())
    if activate:
        if command01:
            print("Human says: " + humanString)
            # addEntry(log, "Muting voice.")
            print("Muting voice.")
            robot.set_robot_volume(0)
            listen_robot(robot)
            humanString = listen_robot.parsedText
        elif command02:
            print("Human says: " + humanString)
            # addEntry(log, "Cozmo voice low.")
            print("Cozmo voice low.")
            robot.set_robot_volume(0.2)
            robot.say_text("Voice lowered.", use_cozmo_voice=True, duration_scalar=0.6, voice_pitch=0).wait_for_completed()
            listen_robot(robot)
            humanString = listen_robot.parsedText
        elif command03:
            print("Human says: " + humanString)
            # addEntry(log, "Cozmo voice higher.")
            print("Cozmo voice higher.")
            robot.set_robot_volume(0.5)
            robot.say_text("Voice higher.", use_cozmo_voice=True, duration_scalar=0.6, voice_pitch=0).wait_for_completed()
            listen_robot(robot)
            humanString = listen_robot.parsedText
        elif command04:
            print("Human says: " + humanString)
            # addEntry(log, "Cozmo voice maximum.")
            print("Cozmo voice maximum.")
            robot.set_robot_volume(1.0)
            robot.say_text("Voice set to maximum level.", use_cozmo_voice=True, duration_scalar=0.6, voice_pitch=0).wait_for_completed()
            listen_robot(robot)
            humanString = listen_robot.parsedText
    else:
        return


def check_photo(robot):
    global humanString
    activate = set(name).intersection(humanString.split())
    command = set(cmd_photo).intersection(humanString.split())
    if activate and command:
        print("Human says: " + humanString)
        # addEntry(log, "Human says: " + humanString)
        take_photo(robot)
        listen_robot(robot)
        humanString = listen_robot.parsedText
    else:
        return


def check_freeplay(robot):
    global humanString
    activate = set(name).intersection(humanString.split())
    command = set(cmd_freeplay).intersection(humanString.split())
    if activate and command:
        print("Human says: " + humanString)
        # addEntry(log, "Human says: " + humanString)
        freeplay(robot)
        listen_robot(robot)
        humanString = listen_robot.parsedText
    else:
        return


# Setup robot functionality #
# (Here we place actions that we may need to call individually from the voice commands.)
def partytime(robot):
    # Triggers don't always play the same action (better for more natural behavior). For a simple animation use:
    # robot.play_anim("anim_speedtap_wingame_intensity02_01").wait_for_completed()
    robot.play_anim_trigger(cozmo.anim.Triggers.DanceMambo).wait_for_completed()


def singing(robot):
    robot.play_anim("anim_cozmosings_getin_01").wait_for_completed()
    robot.play_anim("anim_cozmosings_120_song_01").wait_for_completed()
    # Alternative available songs
    # robot.play_anim("anim_cozmosings_80_song_01").wait_for_completed()
    # robot.play_anim("anim_cozmosings_100_song_01").wait_for_completed()
    robot.play_anim("anim_cozmosings_getout_01").wait_for_completed()


def clock(robot):
    current_directory = os.path.dirname(os.path.realpath(__file__))
    time_now = (datetime.datetime.now().strftime("%H%M"))
    time_speech = (datetime.datetime.now().strftime("%-I %M %p"))
    png = os.path.join(current_directory, "clock_faces", time_now + ".png")

    # load some images and convert them for display cozmo's face
    image_settings = [(png, Image.BICUBIC)]
    face_images = []

    for image_name, resampling_mode in image_settings:
        image = Image.open(image_name)

        # resize to fit on Cozmo's face screen
        resized_image = image.resize(cozmo.oled_face.dimensions(), resampling_mode)

        # convert the image to the format used by the oled screen
        face_image = cozmo.oled_face.convert_image_to_screen_data(resized_image, invert_image=True)
        face_images.append(face_image)

    for image in face_images:
        print("Human says: " + humanString)
        # addEntry(log, "Human says: " + humanString)
        robot.set_head_angle(degrees(35)).wait_for_completed()
        print("time_now = ", time_now)
        print("time_speech = ", time_speech)
        robot.display_oled_face_image(image, 2.0 * 1000.0)
        time.sleep(2.5)
        robot.say_text("The time now is " + time_speech, use_cozmo_voice=True, duration_scalar=0.6, voice_pitch=0) \
            .wait_for_completed()


def random_anim(robot):
    # grab a list of animation triggers
    all_animation_triggers = robot.anim_triggers
    # randomly shuffle the animations
    random.shuffle(all_animation_triggers)
    # select x amount of animations from the shuffled list
    triggers = 1
    # Grab animation. Alt option: Select triggers that have 'WinGame' in their name
    # chosen_triggers = [trigger for trigger in robot.anim_triggers if 'WinGame' in trigger.name]
    chosen_triggers = all_animation_triggers[:triggers]
    # play the random animations one after the other, waiting for each to complete
    for trigger in chosen_triggers:
        robot.play_anim_trigger(trigger).wait_for_completed()


def bored_anim(robot):
    rnd = randint(0, 2)

    try:
        if rnd == 0:
            # Grab animation trigger. You can sub the event with Hiccup / CodeLab123Go / PeekABooNoUserInteraction
            robot.play_anim_trigger(cozmo.anim.Triggers.NothingToDoBoredEvent, in_parallel=True)
    except cozmo.exceptions.RobotBusy:
        return


def wake_up(robot):
    global user_name
    t = (datetime.datetime.now().strftime("%H"))
    greet = None

    if t >= "20":
        greet = "Good evening "
    elif t >= "16":
        greet = "Good afternoon "
    elif t >= "12":
        greet = "Good day "
    else:
        greet = "Good morning "
    if robot.is_on_charger:
        checkBattery(robot)
        robot.set_head_angle(degrees(30)).wait_for_completed()
        robot.set_all_backpack_lights(cozmo.lights.green_light)
        robot.play_anim_trigger(cozmo.anim.Triggers.ConnectWakeUp).wait_for_completed()
        robot.drive_off_charger_contacts().wait_for_completed()
        robot.drive_straight(distance_mm(150), speed_mmps(150)).wait_for_completed()
        robot.set_head_angle(degrees(35), in_parallel=True).wait_for_completed()
        robot.turn_in_place(degrees(5)).wait_for_completed()
        robot.turn_in_place(degrees(-5)).wait_for_completed()
        robot.play_anim('anim_freeplay_reacttoface_like_01').wait_for_completed()
        ask_name(robot)
        user_name = ask_name.parsedText
        robot.say_text(greet + user_name + ". Entering FreePlay mode.",
                       use_cozmo_voice=True, duration_scalar=0.6, voice_pitch=0).wait_for_completed()
        print("Cozmo says: " + greet + user_name + ". Entering FreePlay mode.")
    elif robot:
        checkBattery(robot)
        robot.set_all_backpack_lights(cozmo.lights.off_light)
        robot.set_head_angle(degrees(30)).wait_for_completed()
        robot.drive_straight(distance_mm(30), speed_mmps(150), in_parallel=True).wait_for_completed()
        robot.turn_in_place(degrees(5)).wait_for_completed()
        robot.turn_in_place(degrees(-5)).wait_for_completed()
        robot.play_anim('anim_freeplay_reacttoface_like_01').wait_for_completed()
        ask_name(robot)
        user_name = ask_name.parsedText
        robot.say_text(greet + user_name + ". Entering FreePlay mode.",
                       use_cozmo_voice=True, duration_scalar=0.6, voice_pitch=0).wait_for_completed()
        print("Cozmo says: " + greet + user_name + ". Entering FreePlay mode.")


def checkBattery(robot):
    if robot.battery_voltage <= 3.5:
        color = "red"
    else:
        color = "yellow"
    cprint("BATTERY LEVEL: %f" % robot.battery_voltage + "v\n (Low < 3.5v)", color)


def flash_backpack(robot, flag):
    robot.set_all_backpack_lights(cozmo.lights.green_light.flash() if flag else cozmo.lights.off_light)


def take_photo(robot):
    robot.camera.image_stream_enabled = True
    print("Taking a picture...")
    message = ""
    pic_filename = "cozmo_pic_" + str(int(time.time())) + ".png"
    robot.say_text("Say cheese!").wait_for_completed()
    robot.play_audio(cozmo.audio.AudioEvents.Sfx_Flappy_Increase)
    latest_image = robot.world.latest_image
    if latest_image:
        latest_image.raw_image.convert('L').save(pic_filename)
        message = "picture saved as: " + pic_filename
    else:
        message = "no picture saved"
    robot.camera.image_stream_enabled = False
    return message


def freeplay(robot):
    rec = sr.Recognizer()
    microphone = sr.Microphone(device_index=2)

    print()
    cprint("==========================", "green", attrs=['bold'])
    cprint("= Entering FreePlay Mode =", "green", attrs=['bold'])
    cprint("==========================", "green", attrs=['bold'])
    print()
    cprint("Cozmo is now in full autonomous mode. \n"
           "He will freely explore his environment until he hears the wakeup command ", "green", end=''), \
    cprint("'Cozmo listen'", "cyan", attrs=['bold'])

    while True:
        robot.start_freeplay_behaviors()
        time.sleep(interval)

        with microphone as source:
            rec.pause_threshold = 0.6
            rec.energy_threshold = 4000
            rec.dynamic_energy_threshold = True  # was True
            rec.adjust_for_ambient_noise(source, duration=1)

            try:
                cprint("Listening for wakeup command now.", "cyan")
                # robot.play_audio(cozmo.audio.AudioEvents.Sfx_Morse_Code_Dot)  # Beep sound
                voice = rec.listen(source, timeout=5)
                p = rec.recognize_google(voice)  # Recognizing audio
                robot.play_audio(cozmo.audio.AudioEvents.Sfx_Morse_Code_Dash)  # Rec ok sound

                if p == "Cosmo" or p == "hey Cosmo listen" or p == "Cosmo listen" or p == "cosmopolitan" \
                        or p == "hey cosmopolitan" or p == "hey Cosmo Nissan":
                    cprint("Found. Exiting FreePlay mode. Please wait...", "green")
                    robot.stop_freeplay_behaviors()
                    robot.say_text("Wait a moment please...", use_cozmo_voice=True, duration_scalar=0.6,
                                   voice_pitch=0).wait_for_completed()
                    return
                else:
                    continue

            except sr.WaitTimeoutError:
                cprint("Timeout. Checking again in ", "red", end=''), \
                cprint(str(interval), "red", attrs=['bold'], end=''), cprint(" seconds.", "red")
                continue
            except sr.UnknownValueError:
                cprint("Not found. Checking again in ", "yellow", end=''), \
                cprint(str(interval), "yellow", attrs=['bold'], end=''), cprint(" seconds.", "yellow")
                continue


def ask_name(robot):
    rec = sr.Recognizer()
    microphone = sr.Microphone(device_index=2)
    cprint("\nWhat's your name please?", "white", attrs=['bold'])
    robot.say_text("What's your name please?", use_cozmo_voice=True, duration_scalar=0.6, voice_pitch=0) \
        .wait_for_completed()

    with microphone as source:
        rec.pause_threshold = 0.6
        rec.energy_threshold = 4000
        rec.dynamic_energy_threshold = True  # was True
        rec.adjust_for_ambient_noise(source, duration=1)

        try:
            cprint("Listening...", "white", attrs=['bold'])
            robot.play_audio(cozmo.audio.AudioEvents.Sfx_Morse_Code_Dot)  # Beep sound
            voice = rec.listen(source, timeout=5)  # Recording audio
            cprint("Recognized.", "green")
            robot.play_audio(cozmo.audio.AudioEvents.Sfx_Morse_Code_Dash)  # Rec ok sound
            ask_name.parsedText = rec.recognize_google(voice)  # Recognizing audio
        except sr.WaitTimeoutError:
            robot.say_text("I'm sorry. I didn't get that. ", use_cozmo_voice=True, duration_scalar=0.6, voice_pitch=0) \
                .wait_for_completed()
            cprint("Retrying...", "yellow")
            ask_name(robot)
        except sr.UnknownValueError:
            robot.say_text("I'm sorry. I didn't get that. ", use_cozmo_voice=True, duration_scalar=0.6, voice_pitch=0) \
                .wait_for_completed()
            cprint("Retrying...", "yellow")
            ask_name(robot)
        except sr.RequestError as e:
            robot.say_text("I'm sorry. Cannot connect to voice services. Exiting program.", use_cozmo_voice=True,
                           duration_scalar=0.6, voice_pitch=0).wait_for_completed()
            cprint("Could not request results from Speech Recognition service; {0}".format(e), "red")
            sys.exit(0)


# Setup program functionality #
def printSupportedCommands():
    cprint("You can issue voice commands to Cozmo in a natural language. Always start with wakeup keyword 'Cozmo' and "
           "follow with your command.", "green")
    cprint("Here is a list with", "green", end=''), cprint(" keywords ", "green", attrs=['bold'], end=''), \
    cprint("and", "green", end=''), cprint(" command ", "green", attrs=['bold'], end=''), cprint("examples:", "green")
    # cprint("['forward', 'back', 'left', 'right'] : ", "cyan", end=''), cprint("Cozmo go forward.", "white",
    # attrs=['bold'])
    # cprint(str(cmd_arm) + " : ", "cyan", end=''), cprint("Cozmo lift your arm.", "white", attrs=['bold'])
    # cprint(str(cmd_head) + " : ", "cyan", end=''), cprint("Cozmo look up please.", "white", attrs=['bold'])
    # cprint(str(cmd_follow) + " : ", "cyan", end=''), cprint("Cozmo follow my face.", "white", attrs=['bold'])
    cprint(str(cmd_photo) + " : ", "cyan", end=''), cprint("Cozmo take a photo.", "white", attrs=['bold'])
    # cprint(str(cmd_blocks) + " : ", "cyan", end=''), cprint("Cozmo play with your blocks.", "white", attrs=['bold'])
    cprint(str(cmd_dance) + " : ", "cyan", end=''), cprint("Cozmo dance around.", "white", attrs=['bold'])
    cprint(str(cmd_sing) + " : ", "cyan", end=''), cprint("Cozmo sing me a song.", "white", attrs=['bold'])
    cprint(str(cmd_music_rock) + " : ", "cyan", end=''), cprint("Cozmo play some rock music.", "white", attrs=['bold'])
    cprint(str(cmd_music_favourites) + " : ", "cyan", end=''), cprint("Cozmo play my favourite songs.",
                                                                      "white", attrs=['bold'])
    cprint(str(cmd_music_stop) + " : ", "cyan", end=''), cprint("Cozmo stop the music.", "white", attrs=['bold'])
    cprint(str(cmd_weather_tomorrow) + " : ", "cyan", end=''), cprint("Cozmo what's the weather tomorrow?", "white",
                                                                      attrs=['bold'])
    cprint(str(cmd_weather_forecast) + " : ", "cyan", end=''), cprint("Cozmo what's the forecast for the next days?",
                                                                      "white", attrs=['bold'])
    cprint(str(cmd_time) + " : ", "cyan", end=''), cprint("Cozmo what's the time now?", "white", attrs=['bold'])
    # cprint(str(cmd_sleep) + " : ", "cyan", end=''), cprint("Cozmo go to sleep.", "white", attrs=['bold'])
    # cprint(str(cmd_charge) + " : ", "cyan", end=''), cprint("Cozmo go to your charger.", "white", attrs=['bold'])
    cprint("['mute', 'lower', 'raise', 'voice', 'maximum'] : ", "cyan", end=''), cprint("Cozmo lower your voice.",
                                                                                        "white", attrs=['bold'])
    cprint(str(cmd_exit) + " : ", "cyan", end=''), cprint("Cozmo exit program please.", "white", attrs=['bold'])
    cprint("['FreePlay'] : ", "cyan", end=''), cprint("Cozmo activate FreePlay mode.",
                                                                                        "white", attrs=['bold'])


def listen_robot(robot):
    rec = sr.Recognizer()
    microphone = sr.Microphone(device_index=2)

    with microphone as source:
        rec.pause_threshold = 0.6
        rec.energy_threshold = 4000
        rec.dynamic_energy_threshold = True  # was True
        rec.adjust_for_ambient_noise(source, duration=1)

        try:
            cprint("Listening...", "white", attrs=['bold'])
            robot.play_audio(cozmo.audio.AudioEvents.Sfx_Morse_Code_Dot)  # Beep sound
            voice = rec.listen(source, timeout=10)  # Recording audio
            cprint("Done Listening: recognizing...", "green")
            robot.play_audio(cozmo.audio.AudioEvents.Sfx_Morse_Code_Dash)  # Rec ok sound
            listen_robot.parsedText = rec.recognize_google(voice)  # Recognizing audio
        except sr.WaitTimeoutError:
            cprint("Timeout...", "red")
            listen_robot.parsedText = " "
        except sr.UnknownValueError:
            cprint("Could not understand audio. Retrying...", "yellow")
            listen_robot(robot)
        except sr.RequestError as e:
            robot.say_text("I'm sorry. Cannot connect to voice services. Exiting program.", use_cozmo_voice=True,
                           duration_scalar=0.6, voice_pitch=0) \
                .wait_for_completed()
            cprint("Could not request results from Speech Recognition service; {0}".format(e), "red")
            sys.exit(0)


def initLog():
    global log
    try:
        log = open("log.txt", "a")
    except IOError:
        print("Error opening log file!")
        sys.exit(0)
    else:
        print("Log file opened.")

    return log


def addEntry(log, entry):
    entryTime = time.gmtime()

    # Time format: Day-Month-Year Hour:Minute:Second
    parsedTime = "{0}-{1}-{2} {3}:{4}:{5}".format(str(entryTime.tm_mday), str(entryTime.tm_mon), str(entryTime.tm_year),
                                                  str(entryTime.tm_hour), str(entryTime.tm_min), str(entryTime.tm_sec))

    # Now we patch together the log message
    logMessage = parsedTime + "# " + entry

    # Let's try to log it. If it fails, we simply skip logging the message
    try:
        log.write(logMessage + "\n")
    except IOError:
        print("Error logging message! Skipping...")


def weather():
    # New alternative service: http://rss.accuweather.com/rss/liveweather_rss.asp?metric=1&locCode=Helsinki
    # ==== Weather module initialization start ====
    global tomorrow_response, forecast_response
    # IP Location
    response_ip = requests.get(ip_url)
    ip = response_ip.json()
    location = ip["loc"]

    # Store complete_url variable
    complete_url = base_url + api_key + location + parms
    # Request data
    response = requests.get(complete_url)
    j = response.json()

    # Pass main values
    city = ip["city"]
    current = j["currently"]
    detailed = j["hourly"]
    forecast = j["daily"]

    # Tomorrow's weather
    summary1 = current["summary"]
    summary2 = detailed["summary"]
    try:
        sunrise = dtm.fromtimestamp(forecast["data"][0]["sunriseTime"]).strftime("%I:%M %p")
    except KeyError:
        sunrise = "-"
    try:
        sunset = dtm.fromtimestamp(forecast["data"][0]["sunsetTime"]).strftime("%I:%M %p")
    except KeyError:
        sunset = "-"
    current_temp = round(current["temperature"])
    min_temp = round(forecast["data"][0]["temperatureMin"])
    max_temp = round(forecast["data"][0]["temperatureMax"])

    tomorrow_response = ("In " + city + " will be " + summary2.lower() + " with temperatures from "
                         + str(min_temp) + " degrees celcius to " + str(max_temp)
                         + " degrees celcius. \nThe sun will rise at " + sunrise + " and set at " + sunset
                         + ". \nRight now it is " + str(current_temp) + " degrees celcius and " + summary1.lower()
                         + ".")

    # 3 day Forecast
    fc_summary = forecast["summary"]
    Day_1 = dtm.fromtimestamp(forecast["data"][1]["time"]).strftime("%A")
    Day_1_summary = str(forecast["data"][1]["summary"])
    Day_1_min = round(forecast["data"][1]["temperatureMin"])
    Day_1_max = round(forecast["data"][1]["temperatureMax"])

    Day_2 = dtm.fromtimestamp(forecast["data"][2]["time"]).strftime("%A")
    Day_2_summary = forecast["data"][2]["summary"]
    Day_2_min = round(forecast["data"][2]["temperatureMin"])
    Day_2_max = round(forecast["data"][2]["temperatureMax"])

    Day_3 = dtm.fromtimestamp(forecast["data"][3]["time"]).strftime("%A")
    Day_3_summary = forecast["data"][3]["summary"]
    Day_3_min = round(forecast["data"][3]["temperatureMin"])
    Day_3_max = round(forecast["data"][3]["temperatureMax"])

    data = ("In " + city + " " + Day_1 + " will be " + Day_1_summary.lower() + " with " + str(Day_1_min) + " to "
            + str(Day_1_max) + " degrees celcius. \n" + Day_2 + " will be " + Day_2_summary.lower() + " with "
            + str(Day_2_min) + " to " + str(Day_2_max) + " degrees. \n" + Day_3 + " will be "
            + Day_3_summary.lower() + " with " + str(Day_3_min) + " to " + str(Day_3_max) + " degrees.")

    forecast_response = (data[:254] + '') if len(data) > 254 else data


def readystate_complete(d):
    # AFAICT Selenium offers no better way to wait for the document to be loaded,
    # if one is in ignorance of its contents.
    return d.execute_script("return document.readyState") == "complete"


class AIBot:

    def __init__(self):

        # Initialize selenium options
        self.opts = Options()
        self.opts.add_argument("-headless")
        self.browser = webdriver.Firefox(options=self.opts)
        self.url = "http://demo.vhost.pandorabots.com/pandora/talk?botid=b0dafd24ee35a477"

    def get_form(self):

        # Find the form tag to enter your message
        self.browser.implicitly_wait(10.0)
        self.elem = self.browser.find_element_by_name('input')

    def send_input(self, userInput):

        # Submits your message
        fOne = '<\/?[a-z]+>|<DOCTYPE'
        fTwo = '/<[^>]+>/g'
        while True:
            try:
                self.elem.send_keys(userInput + Keys.RETURN)
            except BrokenPipeError:
                continue
            break

    def get_response(self):
        response = None
        try:
            WebDriverWait(self.browser, 30).until(readystate_complete)
        except WebDriverException:
            pass

        # Retrieves response message
        while True:
            try:
                jFetch = get("http://code.jquery.com/jquery-2.1.1.min.js").content.decode('utf8')
                self.browser.execute_script(jFetch)
                data = self.browser.execute_script("""
                  try {
                  main_str = $;
                  var main_str = $('font:has(b:contains("Chomsky:"))').contents().has( "br" ).last().text().trim();
                  main_str = main_str.replace(/Chomsky:/gi,'').replace(/Chomsky/gi,'Cozmo')
                  .replace(/Wikipedia is a great online encyclopedia./gi, 'Wikipedia is your friend. Use it.')
                  .replace(/click here./gi, 'use a computer browser.')
                  .replace(/^\\s*[\\r\\n]/gm, '');
                  return main_str;
                  }
                  catch(error) {
                  return main_str;
                  }
                """)
                response = (data[:254] + '') if len(data) > 254 else data
            except BrokenPipeError:
                AIBot().get_response()
            return response


# TOFO: Change to new weather service. (Thanks Apple!) http://rss.accuweather.com/rss/liveweather_rss.asp?metric=1&locCode=Helsinki
# TODO: Add bored events to random times if not doing anything (anim_bored_event_01 through to 04)
# TODO: Add face animations for weather, music, etc Note: anim_meetcozmo_lookface_getout is great for DING sound.
# TODO: Add movement commands
# TODO: Randomize dance routines
# TODO: Make Cozmo say something and go to sleep with animation.
# TODO: Add pick me up ability
# TODO: Capture all exceptions
# IMPROVE: Have Cozmo return to base before exiting.
# IMPROVE: Move to new Google Voice API https://pythonspot.com/speech-recognition-using-google-speech-api/
# OPTIMIZE: Clean up code


# ENTRY POINT #
if __name__ == "__main__":
    initCozmo()
