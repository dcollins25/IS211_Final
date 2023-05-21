# IS211 - Professor Ledon - Spring, 2023

Dan Collins - Final Project - Book Catalogue

This application works and has some of the extra credit functionality. 

When the application is first run, it requires the user to register by clicking a link. This is simple, you just supply a new username and new password and then you are registered. From there, you are redirected back to the login.

I did create a testuser \ testuser that still exists just to verify it works before submitting the program. That user is still there but has no books stored.

The application also has the ability to search by title. The search page has a drop-down menu allowing you to choose between ISBN and Title.

Some books returned a whole bunch of books in the JSON response. For these, I made it so the program returned the first book in the list that had the most complete information (ex, title, auther, page-count, avg-rating). I also filtered out books that were summaries of other books (example, "Summary of 80/20 Running").

I was looking to clone a GitHub repository that you created for the final but didn't see one, so I created:
	- https://github.com/dcollins25/IS211_Final