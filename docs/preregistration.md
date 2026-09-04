# Preregistration
## Project

Content Opportunity Intelligence

## Date

2026-09-04

## Why I am writing this first

Before collecting and analyzing the data, I want to write down what I expect to find and how I will test it.

This is mainly to avoid changing the rules later just because I see an interesting result in the data.

If the results are different from what I expected, I will keep the original hypothesis and report what actually happened.

## H1: Which category has the biggest opportunity?

My main hypothesis is:

**K drama will have the biggest gap between audience demand and content competition.**

The four categories in this project are:

1. Anime
2. K drama
3. Animated film
4. Anglophone animation

### How I will test this

For every title, I will calculate a demand score and a competition score.

Because the four categories have different levels of popularity, I will compare titles within their own category rather than putting every title into one overall ranking.

I will then calculate:

**Opportunity gap = Demand percentile − Competition percentile**

After that, I will compare the median opportunity gap for each category.

I will report the result even if K drama does not come out on top.

## H2: Does popularity mean people actually like a title?

My second hypothesis is:

**Search demand and audience ratings will not be strongly related.**

The reason I want to test this is that a title can be searched a lot without necessarily being highly rated.

For example, a controversial or heavily promoted show might receive a lot of attention but have an average rating.

I will compare demand with audience reception and report the strength of the relationship.

## H3: Does my Opportunity Score add anything beyond popularity?

This is an important test for the project.

My hypothesis is:

**The Opportunity Score will produce a meaningfully different ranking from TMDB popularity.**

TMDB popularity will be used as a benchmark and as part of the sampling process.

It will not be included as a direct component of the Opportunity Score.

I will compare the two rankings using:

1. Rank correlation
2. Top 10 overlap

If my Opportunity Score ends up looking almost identical to TMDB popularity, I will report that honestly.

That would mean the scoring system is not adding much beyond a simple popularity ranking.

## What I will not do

I will not change the hypotheses or scoring rules just to make the final results look better.

If a hypothesis is wrong, that is still a useful result.

If the results are unclear, I will say they are unclear rather than forcing a conclusion.

## If I need to change something later

Sometimes a real problem may be discovered while building the project.

If I need to change an important decision after this document is committed, I will record:

1. What I changed
2. Why I changed it
3. The date of the change
4. What the original approach was
5. What the new approach is
6. Whether the change could affect the results
