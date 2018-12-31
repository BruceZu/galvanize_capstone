# Project Overview

This project is an attempt to predict whether a bill or a joint resolution will gather enough votes to pass both chambers of Congress. Upon my research into this subject, it surprised me that fewer than 10% of anything introduced in Congress ever make it into law. The graphic below should give you an idea of the (astonishing?) number of bills that get introduced and the proportion of those that actually become law since 2007.

![Bill Histogram](img/bill_histogram.png)

This project is an attempt to predict whether a bill or joint resolution will pass both chambers of Congress and - assuming that the President will sign it - thus, become law. The focus was initially only on bills and joint resolutions because other forms of legislation, such as simple and concurrent resolutions, do not carry the force of law when passed. Check out [Legislation, Laws, and Acts](https://www.senate.gov/legislative/common/briefing/leg_laws_acts.htm) for definitions and examples.

The predictions will be primarily based on natural language processing of the text of the bill. I also hope to enhance these predictions using decision trees to determine other important features, such as word/character counts, party affiliation of the sponsor of the legislation, number of cosponsors, the date the legislation was introduced, number of amendments, etc.


## Resources

### Local Machine and AWS
Most of the work done for this project started on a local machine. Messages were regularly included in the code to print out to the terminal to notify the user of the process status and whether any errors occurred during a process. Best practice of this would be to have these messages print out to a log.

![system_out_messages](img/system_out_messages.png)

Once it was felt that a process (i.e. web scraping) was working with relatively few errors, the code was migrated into a Ubuntu 18.04 EC2 instance in [Amazon Web Services](https://aws.amazon.com). The EC2 instance is, ultimately, where the modeling and interaction with the data and predictions will occur.


### Python and Mongo
Python was used to scrape the initial data from [congress.gov](https://www.congress.gov/search?q={%22source%22:%22legislation%22}&pageSize=250) using the Requests and BeautifulSoup packages. The data collected was put into json lines format and stored into a collections in a Mongo database. 



## The Process

### Step 1: Data Wrangling
To begin, general information from bills and joint resolutions were scraped from the Legislation search pages on [congress.gov](https://www.congress.gov/search?q={%22source%22:%22legislation%22}&pageSize=250). 

![Legislation Search Page](img/legislation_search.png)

From these pages, most fields and url links for each piece of legislation were scraped and dumped into a Mongo database for analysis. Since there were almost 450 web pages to be scraped, four processes were threaded and joined to gather this data quickly. 

Once in Mongo, this data was then pulled to scrape additional bill details - such as the bill text, the number of amendments, and cosponsor information - from the urls stored.

### Step 2: Labeling
The process for labeling mirrored the [process](https://www.usa.gov/how-laws-are-made) that a bill must undergo to become law. For this project, if a bill or joint resolution gathered enough votes to pass both the Senate and the House of Representatives, it was labeled as 'passed', or '1'. If it failed in one chamber, failed in committee, or never got voted on by the end of the legislative session, it was labeled as 'not passed', or '0'. Those remaining were deemed 'in progress' and labeled with a 'null'.

![Labeling](img/Labeling.png)

### Step 2: Modeling

