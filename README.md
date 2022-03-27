For this project, we decided to build a ChatBot capable of exchanging text messages with a human. 
The goal of this bot is to give book recommendations to an individual.
A human can therefore inform our bot of all the books he has read. 
Once this information is transmitted, our algorithm records a list of these books. 
So you can talk normally with the bot to say hello, you can also get information about the books and finally get recommendations. 
So, to be able to give recommendations, we have loaded a large database that contains the books already read by people and the rating given by them.
When you give our ChatBot the list of books you have already read, it will search its database for people who have read similar books. Thanks to this and to the ratings given to the books, our algorithm can recommend books that the user might like.
To recommend books we pickle a matrix that we created before with our model that give similarities between books. Then, we multiply the list of books which is a vector with the matrix and it returns 
