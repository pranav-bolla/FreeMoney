import praw
import pandas as pd

class RedditScraper:
    def __init__(self, client_id, client_secret, user_agent, subreddit_name):
        self.reddit = praw.Reddit(client_id=client_id,
                                  client_secret=client_secret,
                                  user_agent=user_agent)
        self.subreddit_name = subreddit_name
        self.posts_dict = None  # Store post data here once loaded
    
    def fetch_posts(self, limit=10):

        subreddit = self.reddit.subreddit(self.subreddit_name)
        posts = []
        for submission in subreddit.top("week", limit=limit):  # Fetch top posts of the week
            if submission.selftext:  # Ensure there's text in the post
                posts.append({
                    "title": submission.title,
                    "text": submission.selftext
                })
        return posts

    def get_subreddit_info(self):
        subreddit = self.reddit.subreddit(self.subreddit_name)
        return {
            "Display Name": subreddit.display_name,
            "Title": subreddit.title,
            "Description": subreddit.description
        }
    
    def get_hot_posts(self, limit=5):
        subreddit = self.reddit.subreddit(self.subreddit_name)
        return [post.title for post in subreddit.hot(limit=limit)]
    
    def get_top_posts(self, timeframe="month"):
        subreddit = self.reddit.subreddit(self.subreddit_name)
        posts = subreddit.top(timeframe)
        
        self.posts_dict = {
            "Title": [],
            "Post Text": [],
            "ID": [],
            "Score": [],
            "Total Comments": [],
            "Post URL": []
        }
        
        for post in posts:
            self.posts_dict["Title"].append(post.title)
            self.posts_dict["Post Text"].append(post.selftext)
            self.posts_dict["ID"].append(post.id)
            self.posts_dict["Score"].append(post.score)
            self.posts_dict["Total Comments"].append(post.num_comments)
            self.posts_dict["Post URL"].append(post.url)
        
        return pd.DataFrame(self.posts_dict)
    
    def save_posts_to_csv(self, df, filename="Top Posts.csv"):
        df.to_csv(filename, index=True)
    
    def get_posts_dict(self):
        if self.posts_dict is None:
            raise ValueError("No post data loaded. Call `get_top_posts` first.")
        return self.posts_dict