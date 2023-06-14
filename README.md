# haikuLambda
A Lambda function implementation of a Slack app that responds to messages that fit the strict Haiku pattern (5-7-5)

For example, if someone asks:

```
[User]: Nicholas Cage has a new movie...anyone want to go see it?
```

This bot responds with:

> Nicholas Cage has
> 
> A new movie... anyone
> 
> Want to go see it?

-[User]

# Use
Deploy in a Lambda function behind API Gateway; requires the `Requests` python library in a Lambda layer and a RapidAPI account to use the WordsAPI for syllable counts.
