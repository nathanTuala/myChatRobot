import spacy
import telegram
import mysql.connector
import json
from telegram.ext import Updater, MessageHandler, Filters,CommandHandler,ConversationHandler


def extract_intent(doc):
	for token in doc:
		if token.dep_ == 'dobj':
			verb = token.head.text
			dobj = token.text
	#Create a list of tuples for possible verb synonyms
	verbList = [('order','want','give','make'),('show','find')]
	#find the tuple containing the transitive verb extracted from the sample
	verbSyns = [item for item in verbList if verb in item]
	#create a list of tuples for possible direct object synonyms
	dobjList = [('pizza','pie','dish'),('cola','soda')]
	#find the tuple containing the direct object extracted from the sample
	dobjSyns = [item for item in dobjList if dobj in item]
	#replace the transitive verb and the direct object with synonyms supported by the application
	#and compose the string that represents the intent
	if len(verbSyns) == 0 or len(dobjSyns) == 0:
		intent = 'unrecognized'
	else:
		intent = verbSyns[0][0] + dobjSyns[0][0].capitalize()
	return intent
# Transforms a dictionary into a string
def details_to_str(user_data):
	details = list()
	for key, value in user_data.items():
		details.append('{} - {}'.format(key, value))
	return "\n".join(details).join(['\n', '\n'])
# Initialize conversation with the user
def start(update, context):
	update.message.reply_text('Hi! my name is mayele. I can help make a pizza order.')
	return 'ORDERING'
#For simplicity, the intent_exit() can recognize only one intent: orderPizza
def strore_info(dic):
	json_str = json.dumps(dic) # Convert orderdict dictionary into JSON string
	mydb=mysql.connector.connect(
		host="localhost",
		user="root",
		passwd="my_password",
		database="mybot")
	query = ("""INSERT INTO orders (product, ptype, qty)
     SELECT product, ptype, qty FROM
         JSON_TABLE(
          %s,
           "$" COLUMNS(
             qty    INT PATH '$.qty',
             product   VARCHAR(30) PATH "$.product",
             ptype     VARCHAR(30) PATH "$.ptype"
           )
         ) AS jt1""") #Define an insert SQL statement to be passed into the database for processing
	mycursor = mydb.cursor()
	mycursor.execute(query, (json_str,))
	mydb.commit()
# Extract user intent
def intent_ext(update, context):
	msg = update.message.text
	nlp = spacy.load('en')
	doc = nlp(msg)
	for token in doc:
		if token.dep_ == 'dobj':
			intent = extract_intent(doc)
			if intent == 'orderPizza':
				context.user_data['product'] = 'pizza'
				update.message.reply_text('We need some more information to place your order. What type of pizza do you want?')
				return 'ADD_INFO'
			else:
				update.message.reply_text('Your intent is not recognized. Please rephrase your request.')
				return 'ORDERING'
			return
	update.message.reply_text('Please rephrase your request. Be as specific as possible!')
#add_info function is the callback for the ADD_INFO state handler
def add_info(update, context):
	add_info.type = ''
	msg = update.message.text
	nlp = spacy.load('en')
	doc = nlp(msg)
	for token in doc:
		if token.dep_ == 'dobj':
			dobj = token
			for child in dobj.lefts:
				if child.dep_ == 'amod' or child.dep_ == 'compound':
					context.user_data['type'] = child.text
					user_data = context.user_data
					strore_info(user_data)
					update.message.reply_text("Your order has been placed."
                                    "{}"
                                    "Have a nice day!".format(details_to_str(user_data)))
					return ConversationHandler.END
	#In case the User did not provide a full sentence
	for token in doc:
		if token.pos_ == 'PROPN' or token.pos_ == 'NOUN' or token.pos_ == 'ADJ':
			add_info.type = token.text
			update.message.reply_text("Do you want a " + token.text + " pizza?")
			return 'ADD_INFO'
	#Handles yes or no answers
	if len(list(doc)) == 1:
		res = list(doc)[0]
		if(res.text == 'yes'):
			context.user_data['type'] = add_info.type
			user_data = context.user_data
			strore_info(user_data)
			update.message.reply_text("Your order has been placed."
                            "{}"
                            "Have a nice day!".format(details_to_str(user_data)))
			return ConversationHandler.END
	update.message.reply_text("Cannot extract necessary info. Please try again.")
	return 'ADD_INFO'
#cancel() sends a goodbye message to the user and switches the state to ConversationHandler.END
def cancel(update, context):
	update.message.reply_text("Have a nice day!")
	return ConversationHandler.END
def main():
    updater = Updater("my_token", use_context=True)
    disp = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            'ORDERING': [MessageHandler(Filters.text,
                                        intent_ext)
                        ],
            'ADD_INFO': [MessageHandler(Filters.text,
                                        add_info)
                        ],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    disp.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
	main()

