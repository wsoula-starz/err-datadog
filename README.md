# DataDog plugin for Errbot

[![Build Status](https://travis-ci.org/MattHodge/err-datadog.svg?branch=master)](https://travis-ci.org/MattHodge/err-datadog)

Datadog is a plugin for [Errbot](http://errbot.io), a Python-based chat bot.

It allows chat users query DataDog graphs.

## Installation

To install the plugin, tell your bot in a private chat:

```
!repos install https://github.com/MattHodge/errbot-datadog.git
```

## Configuration

You need to configure a DataDog API key and App key.

```
# Get the config template
!plugin config datadog

# Set the config template
!plugin config datadog {'DATADOG_API_KEY': 'XXXXX', 'DATADOG_APP_KEY': 'XXXXXX'}
```
