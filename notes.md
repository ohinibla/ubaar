
# FIX: 
- user needs to be created after otp verification per assignment request.

# BUG:
- possible bug when trying to cache the phonenumber(username) both in login and register views, wouldn't they conflict?

# WARNING:
- check urls in GET

# NOTE: 
- can i authenticate without user and pass, i mean a temporary authentication with otp
- change otp tempalte name accordingly
- move otp equality validation to a validator?
- add elif and else, it's getting hard to follow 
- can move the user ban status check before HTTP methods conditionals
  since doesn't matter whether request is GET or POST, return with an
  error (improved?)
