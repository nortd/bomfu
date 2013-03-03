"""
This configuration file loads environment's specific config settings for the application.
It takes precedence over the config located in the boilerplate package.
"""

import os

if "SERVER_SOFTWARE" in os.environ:
    if os.environ['SERVER_SOFTWARE'].startswith('Dev'):
        from config.localhost import config

    elif os.environ['SERVER_SOFTWARE'].startswith('Google'):
        from config.production import config
else:
    from config.testing import config


config['app_name'] = 'BOMfu'
config['enable_federated_login'] = False

# disable multi-language
config['locales'] = []

# recaptcha
config['captcha_public_key'] = "6Lf4Tt0SAAAAAHhMLHXVsR59thKDtBGPwiqdyHDY"
config['captcha_private_key'] = "6Lf4Tt0SAAAAADNAt2A6dsLLJ6J-ITEGUfiQcOvt"

# google analytics
config['google_analytics_domain'] = "bomfu.com"
config['google_analytics_code'] = "UA-19608069-4"
