# RUI3_AT-lib


This is a wrapper for the RUI3_AT API and was made strictly following the official API documentation: https://docs.rakwireless.com/product-categories/software-apis-and-libraries/rui3/at-command-manual/

The docstrings inside the source code mimic quite precisely what is said in the documentation but, if you happen to have any doubts or there are some documentation clashes, always refer back to the official docs since they are the authoritative source.

The library is built around the node class (RUI3Node) which, when instantiated, will automatically find and connect to, when available, **ONE AND ONLY ONE** RUI3_AT compatible device. Trying to connect multiple devices at once will result in errors and/or undefined behaviour.

All the commands are wrapped inside methods for the RUI3Node class, with the names being as self-explanatory as possible.

Since the API error messages are very generic and unclear, most of the checking for the correctness of the values passed to the methods will be done inside the library, with more descriptive error messages.

While the entirety of the API commands provided in the official documentation has been implemented, not all of them are compatible with all the devices. I suggest running the at_help() method first to verify which commands are available for you particular device, and which ones have read and/or write permissions.

I am in no way associated with RAK nor did I have any contact with them during the making of this library. This is entirely a personal project that I decided to publish.

For any issue, you can contact me at: dev.danielemagnaterra@gmail.com
