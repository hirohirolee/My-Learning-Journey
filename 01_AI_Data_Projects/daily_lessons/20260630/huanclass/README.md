# Scrape Movie - 100 Movies Dataset

This repository contains the crawler code, downloaded poster images, and exported CSV/Excel datasets for all **100 movies** from the SSR scrape practice site (pages 1 to 10).

## How to Run the Scripts

1. **Run the complete pipeline**:
   ```bash
   python crawl_all.py
   ```
   This script executes the entire pipeline:
   - Downloads pages 1 to 10 HTML content and saves them in the `cache/` directory to avoid redundant page loads.
   - Parses the HTML to extract information for all 100 movies.
   - Downloads all 100 poster images concurrently (speeding up download times).
   - Generates [movies.csv](movies.csv) containing all 100 records and Excel-compatible `=IMAGE` formulas.
   - Generates [movies.xlsx](movies.xlsx) formatting the data and embedding all 100 offline poster images directly inside the cells.

## Scraped Data Files

- **Complete Excel Dataset**: [movies.xlsx](movies.xlsx) (approx. 6MB, with all 100 poster images embedded)
- **Complete CSV Dataset**: [movies.csv](movies.csv) (with `=IMAGE` formulas)
- **Local Poster Images**: [posters/](posters/) (contains all 100 poster JPGs)
- **HTML Cache**: [cache/](cache/) (cached pages 1-10)

## Sample Movie List (Page 1 Showcase)

Below is a preview table showing the first 10 movies:

| Poster | Movie Info | Categories | Region / Duration | Release Date | Score |
| :---: | :--- | :--- | :--- | :--- | :---: |
| <img src="posters/1_霸王别姬.jpg" width="80" alt="霸王别姬"/> | **霸王别姬**<br>*Farewell My Concubine* | `剧情` `爱情` | 中国内地、中国香港<br>171 分钟 | 1993-07-26 上映 | **9.5** |
| <img src="posters/2_这个杀手不太冷.jpg" width="80" alt="这个杀手不太冷"/> | **这个杀手不太冷**<br>*Léon* | `剧情` `动作` `犯罪` | 法国<br>110 分钟 | 1994-09-14 上映 | **9.5** |
| <img src="posters/3_肖申克的救赎.jpg" width="80" alt="肖申克的救赎"/> | **肖申克的救赎**<br>*The Shawshank Redemption* | `剧情` `犯罪` | 美国<br>142 分钟 | 1994-09-10 上映 | **9.5** |
| <img src="posters/4_泰坦尼克号.jpg" width="80" alt="泰坦尼克号"/> | **泰坦尼克号**<br>*Titanic* | `剧情` `爱情` `灾难` | 美国<br>194 分钟 | 1998-04-03 上映 | **9.5** |
| <img src="posters/5_罗马假日.jpg" width="80" alt="罗马假日"/> | **罗马假日**<br>*Roman Holiday* | `剧情` `喜剧` `爱情` | 美国<br>118 分钟 | 1953-08-20 上映 | **9.5** |
| <img src="posters/6_唐伯虎点秋香.jpg" width="80" alt="唐伯虎点秋香"/> | **唐伯虎点秋香**<br>*Flirting Scholar* | `喜剧` `爱情` `古装` | 中国香港<br>102 分钟 | 1993-07-01 上映 | **9.5** |
| <img src="posters/7_乱世佳人.jpg" width="80" alt="乱世佳人"/> | **乱世佳人**<br>*Gone with the Wind* | `剧情` `爱情` `历史` `战争` | 美国<br>238 分钟 | 1939-12-15 上映 | **9.5** |
| <img src="posters/8_喜剧之王.jpg" width="80" alt="喜剧之王"/> | **喜剧之王**<br>*The King of Comedy* | `剧情` `喜剧` `爱情` | 中国香港<br>85 分钟 | 1999-02-13 上映 | **9.5** |
| <img src="posters/9_楚门的世界.jpg" width="80" alt="楚门的世界"/> | **楚门的世界**<br>*The Truman Show* | `剧情` `科幻` | 美国<br>103 分钟 | 暂无上映日期 | **9.0** |
| <img src="posters/10_狮子王.jpg" width="80" alt="狮子王"/> | **狮子王**<br>*The Lion King* | `动画` `歌舞` `冒险` | 美国<br>89 分钟 | 1995-07-15 上映 | **9.0** |
