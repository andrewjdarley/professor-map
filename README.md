## Rate-My-Professor MyMAP insert

This project is all about improving the class registration process at BYU in which students frequently write various professor names in Rate My Professor to get an idea which sections are rated the best. It involves regularly scraping Rate My Professor and uploading the ratings and reviews to Supabase. It is presented as a Chrome Extension that integrates directly with MyMAP and displays information right next to the professor name and section times. 

### Demo Video

<video src="https://github.com/andrewjdarley/professor-map/blob/main/demo.webm" controls style="max-width: 100%; height: auto;">
  Video not found
</video>

https://github.com/andrewjdarley/REPO_NAME/raw/main/demo.webm

### What I learned

This project was my first experience integrating a webscraper directly with a database. And I've certainly learned that this is a much better way of working things than just leaving it in json files. Supabase really is great at managing exactly what I avoid doing all the time so I'm going to change my habits. 

This is also only my second Chrome extension and my first time editing the html of webpages using an extension. It is certainly a good skill to be famiiar with. Makes things significantly easier. 

### AI use

I used AI every step of the way. To make the webscraper I shared the request format with AI and had it write a python script, I discussed the structure for the SQL database, and I had its assistance in coding the Extension. Despite this, I made an effort to understand why the things that the AI coded worked along the way and the design decisions were ultimately my own. I am so grateful I had it to write my Javascript for me as that is definitely my weakest of the main languages 😅

### Why is this Interesting to me?

There's a reason that Rate My Professor is so popular. There is a niche to be fulfilled in College tools. I am currently a college student and feel acutely the annoyance that is the registration process so this has some personal significance to me. It's gonna make my next few semesters just a tich easier. 

We're computer scientists. We're willing to spend 30 hours just to save us 5 minutes. 

### Key Learnings

Supabase
Chrome Extensions
HTML Injections

### Scaling and stuff

Honestly, since I'm not expecting much of a load on this database I chose not to spend my time on redundancies and whatnot.

### Please share this!

I'd be thrilled if you were willing to make my project a demonstration for other students!