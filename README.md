# Textbooks
This python program imports book pricing data from bncollege bookstores.  It tries to grab data for every class that's possible.  It will take a long time to run, and it requires mongodb to be up and running.  **It will by default dump everything into `db.test.test` so make sure to change it if you don't want that.

If you want to make this work for your own university, edit the following lines in Main.py
  
    __store_id__ = ''
    __campus_id__ = ''
    __term_id__ = ''
    
You can find these values if you inspect the network requests to select a class.  By default, it gets data for Binghamton University, because Binghamton's a cool school.

You'll need to have some dependencies installed for the code to work, so run `pip install -r requirements.txt` from the repository folder to get what's needed.

##License
All the code in this repository was written by me.  You're free to do whatever you want with my code (MIT license).  However, there's no guarantee that this code isn't going to devlop intelligence and go back in time to kill your mom.  Jokes aside, I'd appreciate it if you share improvements or bug fixes.

##Contributing
Think I did something poorly?  Well, you're probably right.  Everything is in a single mega file with a scary amount of generic try/except statements.  It's crude, but it does get the job done on my machines.  If you want to add a dependency, make sure to add it to `requirements.txt`.  That's really about it, submit a pull request if you want.
