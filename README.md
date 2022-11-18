# Tweetext: Find old tweets with the Wayback Machine

Want to find old tweets and don't know how? You found the solution!

## Features:

- **All** tweets from an account in a text file.

- Can be used with **deleted** accounts.

- The link to view the tweet is **along** with the text file.

- Allows **custom** time range to narrow Tweet search between two dates.

- Ability to switch between a list of proxy servers to avoid 429 errors.<br>
**You will need to do this for datasets larger than about 800 tweets.**

## Usage

```
python3 tweetext.py -u USERNAME [OPTIONS]

    -u, --username                                  Specifies the Twitter handle of the target user

    --batch-size                                    Specifies how many URLs you would like to
                                                    examine at a time. Expecting an integer between
                                                    1 and 100. A higher number will give you faster speed.
                                                    momentum, but with the risk of errors. default = 100

    --semaphore-size                                Specify how many URLs --batch-size you want
                                                    I would like to query asynchronously all at once.
                                                    Expecting an integer between 1 and 50.
                                                    A higher number will give you a speed momentum,
                                                    but with the risk of errors. Default = 50

    -from, --fromdate                               Restricted search of *archived* deleted Tweets
                                                    From this date
                                                    (can be combined with -to)
                                                    (YYYY-MM-DD or YYYY/MM/DD format
                                                    or YYYYMMDD, doesn't matter)


    -to, --todate                                   Restrict search of *archived* deleted Tweets
                                                    on and before this date
                                                    (can be combined with -from)
                                                    (YYYY-MM-DD or YYYY/MM/DD format
                                                    or YYYYMMDD, doesn't matter)


    --proxy-file                                    Provide a list of proxies to use.
                                                    You will need this to check large groups of tweets
                                                    Each line must contain a url:port to use
                                                    The script will choose a new proxy from the
                                                    list randomly after each --batch-size


    Logs                                            After checking a user's tweets, but before you
                                                    make a download selection, a folder will be created
                                                    with that username. This folder will contain a log of:
                                                    <deleted-twitter-url>:<deleted-wayback-url>
                                                    in case you need them
```

```
    Examples:
    python3 tweetext.py -u taylorswift13            Download all tweets
                                                    (until deleted)
                                                    from @taylorswift13

    python3 tweetext.py -u drake -from 2022/09/02   All downloads @drake's
                                                    Tweets (until deleted)
                                                    from the beginning until
                                                    February 9, 2022
```

#### Installation

```
git clone https://github.com/clopso/tweetext
```

```
cd tweetxt
```

```
pip3 install -r requirements.txt
```

Run the command:

```
python3 tweetext.py -u USERNAME

```

(Replace `USERNAME` with your target handle).

For more information, check out the [Usage](#usage) section above.

## Troubleshooting

The default speed settings for `--semaphore-size` and `--batch-size` are set to the fastest possible execution. Reduce these numbers to slow down your execution and reduce the chance of errors.
For checking large numbers of tweets (> than 800) you'll need to use web proxies and `--proxy-file` flag

## Things to keep in mind

- Quality of the HTML files depends on how the Wayback Machine saved them. Some are better than others.
- This tool is best for text. You might have some luck with photos. You cannot download videos.
- Custom date range is not about when Tweets were made, but rather when they were _archived_. For example, a Tweet from 2011 may have been archived today.