# (Inofficial) MOSAIC Telegram Bot

!! The bot is just work in progress

## Introduction

MOSAIC (**M**ultidisciplinary drifting **O**bservatory for the **S**tudy of **A**rctic **C**limate) is the largest arctic scientific research project in history (<https://www.mosaic-expedition.org/).> Hundreds of researches from all around the world are drifting with the german icebreaker Polarstern thru the arctic ocean. To let the world participate in this adventure, they have a web app where they share pictures, stories and weather data (<https://follow.mosaic-expedition.org/>).

The idea behind this bot is to provide this information to the users by using your preferred messenger.

## Features of the bot

- Sending story and pictures to the user by request
  - Latest one (done)
  - Second latest (done)
  - With specific date
  - Message contains
    - Title (done)
    - Small picture (done)
    - Story (done)
    - Link to the appropriate entry in the web app
    - Link to the larger picture
- Sending data of the expedition to the user by request
  - Data
    - Weather
    - Ice extend
  - Message contains
    - Values
    - Graph (like in the MOSAIC web app)
  - Latest one
  - With specific date
- Providing an Inline Keyboard to get
  - Latest Story and picture (done)
  - Calendar
  - Latest weather data
  - Latest ice extend
- Languages
  - German
  - English
- Message language depends on the telegram language
  - Fallback: English
- The date can be requested in several formats
  - Inline Keyboard
  - d.m.y
  - y-m-d
  - m/d/y
  - Month and day can be type with one or 2 digits (d, dd, m, mm)
  - The year can be typed with 2 or 4 digits (yy, yyyy)

## Data download

The data from the app can be downloaded as json file. A separate python program, running as a job, is responsible for the download of the data and for storing it in the directory. The filename of the json file has the format `mosaic_data_<yy>-<mm>-<dd>.json`. The downloader is keeping the files of 4 day's, older files will be deleted. If the bot cannot download a file, nothing happens.

When the bot is requested, he is always looking for a file with the current date. If this file is present, the bot uses this one. If not, the bot falls back to the file of the previous day and so on. If the bot cannot find a file, a error message is provided to the user.
