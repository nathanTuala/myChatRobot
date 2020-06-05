import spacy
import telegram
import wikipedia
from telegram.ext import Updater, MessageHandler, Filters,CommandHandler,ConversationHandler



#Extract user intent
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
	intent = verbSyns[0][0] + dobjSyns[0][0].capitalize()
	if len(verbSyns) == 0 or len(dobjSyns) == 0:
		intent = 'unrecognized'
	else:
		intent = verbSyns[0][0] + dobjSyns[0][0].capitalize()
	return intent
#Converts the user_data dictionary to a string
#user_data contains the kind of pizza and number of pizzas the user wants
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
#the code responsible for interactions with telegram
if __name__ == '__main__':
	main()
