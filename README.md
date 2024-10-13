# academicKeywordHavester
Gather stats of references to software/author from Google Scholar 

## Installation
```
pip3 install scholarly matplotlib 
```

or 
```
pip3 install scholarly matplotlib --break-system-pacakges
```

## Usage 
```
python3 harvestStats.py h # h for help and usage 
```

To query Google Scholar and build an excel database for an author or software,
```
python3 harvestStats.py q 'Yishan Shen' 
```

or 
```
python3 harvestStats.py q EQdyna 3 
```
The last number indicates how many batches of queries to make. A batch contains 20 queries and if not given, the default is 1.
  
If a database exists, use 'p' option to plot the article counts and total citations by year. 
```
python3 harvestStats.py p GMTSAR 
```

## Note
Each query is done every 5 to 10 seconds. We just want an efficient way to get some reference data. Please don't stress Goolge Scholar by sending too many requests in a short time. Otherwise, your IP will be blocked.