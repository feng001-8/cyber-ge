const fs = require('fs');
const path = require('path');

const contentDir = path.join(process.cwd(), 'src/content/scriptures/spoken-english');
const pagesDir = path.join(process.cwd(), 'src/pages/scriptures/spoken-english');

fs.mkdirSync(contentDir, { recursive: true });
fs.mkdirSync(pagesDir, { recursive: true });

const mdShopping = `# 购物篇 (Shopping)

## 1. 进店打招呼 (Greeting)
当走进商店时，店员通常会主动打招呼。掌握一些简单得体的回应方式，能让你在购物时更加从容。

*   **"Just looking, thanks."**
    随便看看，谢谢。（这句非常实用，当你不需要帮助时可以直接使用）
*   **"I'm looking for a pair of shoes."**
    我想找一双鞋。
*   **"Do you carry this brand?"**
    你们卖这个牌子吗？

## 2. 询问价格与尺码 (Price & Size)
在试穿或者购买前，沟通价格与尺码是必不可少的环节。

*   **"How much is this?"**
    这个多少钱？
*   **"Do you have this in a larger size / smaller size?"**
    这个有大一号 / 小一号的吗？
*   **"Can I try this on?"**
    我能试穿一下吗？
*   **"Where is the fitting room?"**
    试衣间在哪里？

## 3. 结账 (Checkout)
确认购买后，前往收银台结账。

*   **"I'll take it."**
    我要买这个。
*   **"Do you accept Apple Pay / Credit Cards?"**
    你们接受 Apple Pay / 信用卡吗？
*   **"Could I have a receipt, please?"**
    能给我小票吗？
*   **"Can I get a tax refund form?"**
    能给我退税单吗？
`;

const mdAirport = `# 机场乘机篇 (Airport)

## 1. 办理登机手续 (Check-in)
到达机场后，第一步是前往值机柜台办理登机牌和行李托运。

*   **"Here is my passport and booking reference."**
    这是我的护照和预订参考号。
*   **"I would like an aisle seat / a window seat, please."**
    我想要一个靠走道 / 靠窗的座位。
*   **"Do I need to check this bag in?"**
    这个包需要托运吗？
*   **"How many bags can I check in for free?"**
    我可以免费托运几件行李？

## 2. 安检 (Security)
安检是机场最严格的环节，听懂工作人员的指令非常重要。

*   **"Please take out your laptop and liquids."**
    请拿出您的笔记本电脑和液体。
*   **"Do I need to take off my shoes?"**
    我需要脱鞋吗？
*   **"Please step through the scanner."**
    请穿过安检门。

## 3. 登机与机上服务 (Boarding & In-flight)
登机后，与乘务员的沟通。

*   **"Could you help me put my bag in the overhead compartment?"**
    能帮我把包放进行李架吗？
*   **"Can I have some water / a blanket, please?"**
    能给我点水 / 一条毯子吗？
*   **"Please fasten your seatbelt."**
    请系好安全带。
`;

const mdDirections = `# 问路篇 (Directions)

## 1. 引起注意 (Getting Attention)
在街上向陌生人问路时，礼貌的开场白能增加获得帮助的几率。

*   **"Excuse me, could you help me?"**
    打扰一下，能帮我个忙吗？
*   **"Sorry to bother you, but I'm lost."**
    抱歉打扰，我迷路了。

## 2. 询问位置 (Asking for Directions)
直接询问目的地或某类设施的位置。

*   **"How do I get to the nearest subway station?"**
    最近的地铁站怎么走？
*   **"Is it far from here?"**
    离这里远吗？
*   **"Which way to the museum?"**
    去博物馆走哪条路？
*   **"Can you show me on the map?"**
    能在地图上指给我看吗？

## 3. 听懂指路 (Understanding Directions)
听懂对方的指路方向词汇。

*   **"Go straight for two blocks."**
    直走两个街区。
*   **"Turn left / right at the next intersection."**
    在下个十字路口左/右转。
*   **"It's on your right."**
    它在你的右边。
*   **"You can't miss it."**
    你不会错过的（非常显眼）。
`;

fs.writeFileSync(path.join(contentDir, '01-shopping.md'), mdShopping.trim());
fs.writeFileSync(path.join(contentDir, '02-airport.md'), mdAirport.trim());
fs.writeFileSync(path.join(contentDir, '03-directions.md'), mdDirections.trim());

const getAstroTemplate = (volume, id, mdFilename) => `---
import Layout from '../../../layouts/Layout.astro';
import { marked } from 'marked';
import fs from 'node:fs';
import path from 'node:path';

// 读取 Markdown 文件
const mdPath = path.join(process.cwd(), 'src/content/scriptures/spoken-english/${mdFilename}');
const mdContent = fs.readFileSync(mdPath, 'utf-8');
let htmlContent = marked(mdContent);

// 修复代码块第一行空白问题
htmlContent = htmlContent.replace(/<code([^>]*)>\\n/g, '<code$1>');

const scripture = {
  symbol: '䷹',
  title: '英语口语学习',
  titleEn: 'Spoken English Learning',
  chapters: [
    { id: 'shopping', volume: 1, title: 'Shopping', titleZh: '购物篇' },
    { id: 'airport', volume: 2, title: 'Airport', titleZh: '机场乘机篇' },
    { id: 'directions', volume: 3, title: 'Directions', titleZh: '问路篇' },
  ]
};

const chapter = scripture.chapters[${volume - 1}];
const prevChapter = ${volume > 1 ? `scripture.chapters[${volume - 2}]` : 'null'};
const nextChapter = ${volume < 3 ? `scripture.chapters[${volume}]` : 'null'};
const readTime = 5;
---

<Layout title={\`\${chapter.titleZh} · \${scripture.title}\`}>
  <main class="relative z-10 flex-grow w-full max-w-[1600px] mx-auto flex flex-col lg:flex-row min-h-[calc(100vh-4rem)]">
    <!-- Sidebar -->
    <aside class="w-full lg:w-72 border-b lg:border-b-0 lg:border-r border-text-main/10 flex-shrink-0 bg-[#FAFAF8] lg:sticky lg:top-16 lg:h-[calc(100vh-4rem)] overflow-y-auto hidden lg:block">
      <div class="p-5 sticky top-0 bg-[#FAFAF8]/95 backdrop-blur-sm z-10 border-b border-text-main/5">
        <a href="/scriptures" class="flex items-center gap-2 text-text-subtle hover:text-jade transition-colors mb-3 text-sm">
          <span class="material-symbols-outlined text-base">arrow_back</span>
          <span>返回书架</span>
        </a>
        <h2 class="font-bold text-lg text-text-main leading-tight">{scripture.title}</h2>
        <p class="text-xs text-text-subtle mt-1">{scripture.titleEn}</p>
      </div>
      <nav class="p-3 space-y-1">
        {scripture.chapters.map((ch, idx) => {
          const isActive = idx === ${volume - 1};
          return (
            <a href={\`/scriptures/spoken-english/\${String(ch.volume).padStart(2, '0')}\`} class={\`group relative block px-4 py-3 rounded-lg transition-all duration-200 \${isActive ? 'bg-jade/10' : 'hover:bg-black/5'}\`}>
              <div class={\`absolute left-0 top-2 bottom-2 w-1 rounded-full transition-all \${isActive ? 'bg-jade' : 'bg-transparent group-hover:bg-jade/30'}\`}></div>
              <div class="flex items-start gap-3">
                <span class={\`font-mono text-xs mt-0.5 \${isActive ? 'text-jade font-bold' : 'text-text-subtle'}\`}>{String(ch.volume).padStart(2, '0')}</span>
                <div>
                  <div class={\`text-sm leading-tight \${isActive ? 'font-bold text-jade' : 'text-text-main'}\`}>{ch.titleZh}</div>
                  <div class="text-xs text-text-subtle mt-0.5">{ch.title}</div>
                </div>
              </div>
            </a>
          );
        })}
      </nav>
    </aside>

    <!-- Main Content -->
    <div class="flex-grow overflow-y-auto">
      <article class="max-w-4xl mx-auto px-6 py-8 lg:py-12">
        <header class="mb-10 pb-8 border-b border-text-main/10">
          <div class="flex items-center gap-3 mb-4">
            <span class="font-mono text-sm text-jade font-bold">第 {chapter.volume} 章</span>
            <span class="text-text-subtle">·</span>
            <span class="text-sm text-text-subtle">约 {readTime} 分钟阅读</span>
          </div>
          <h1 class="text-3xl lg:text-4xl font-bold text-text-main mb-2">{chapter.titleZh}</h1>
          <p class="text-lg text-text-subtle">{chapter.title}</p>
        </header>

        <div class="prose prose-lg max-w-none scripture-content" set:html={htmlContent}>
        </div>

        <!-- Navigation -->
        <nav class="mt-16 pt-8 border-t border-text-main/10 flex justify-between items-center">
          {prevChapter ? (
            <a href={\`/scriptures/spoken-english/\${String(prevChapter.volume).padStart(2, '0')}\`} class="group flex items-center gap-3 text-text-subtle hover:text-jade transition-colors">
              <span class="material-symbols-outlined">arrow_back</span>
              <div>
                <div class="text-xs">上一章</div>
                <div class="font-medium text-text-main group-hover:text-jade">{prevChapter.titleZh}</div>
              </div>
            </a>
          ) : <div></div>}
          {nextChapter ? (
            <a href={\`/scriptures/spoken-english/\${String(nextChapter.volume).padStart(2, '0')}\`} class="group flex items-center gap-3 text-text-subtle hover:text-jade transition-colors text-right">
              <div>
                <div class="text-xs">下一章</div>
                <div class="font-medium text-text-main group-hover:text-jade">{nextChapter.titleZh}</div>
              </div>
              <span class="material-symbols-outlined">arrow_forward</span>
            </a>
          ) : <div></div>}
        </nav>
      </article>
    </div>
  </main>
</Layout>

<style is:global>
  .scripture-content h1 { display: none; }
  .scripture-content h2 {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--color-text-main);
    margin-top: 3rem;
    margin-bottom: 1.5rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid rgba(42, 45, 44, 0.1);
  }
  .scripture-content h3 {
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--color-text-main);
    margin-top: 2rem;
    margin-bottom: 1rem;
  }
  .scripture-content h4 {
    font-size: 1.125rem;
    font-weight: 600;
    color: var(--color-text-main);
    margin-top: 1.5rem;
    margin-bottom: 0.75rem;
  }
  .scripture-content p {
    color: var(--color-text-main);
    line-height: 1.75;
    margin-bottom: 1rem;
  }
  .scripture-content ul, .scripture-content ol {
    margin-bottom: 1rem;
    padding-left: 1.5rem;
  }
  .scripture-content li {
    margin-bottom: 0.5rem;
    color: var(--color-text-main);
  }
  .scripture-content blockquote {
    border-left: 4px solid var(--color-jade);
    background-color: rgba(74, 139, 113, 0.05);
    padding: 1rem 1.5rem;
    margin: 1.5rem 0;
    border-radius: 0 0.5rem 0.5rem 0;
  }
  .scripture-content blockquote p {
    margin-bottom: 0;
  }
  .scripture-content code {
    background-color: #f3f4f6;
    color: #1f2937;
    padding: 0.125rem 0.375rem;
    border-radius: 0.25rem;
    font-size: 0.875rem;
    font-family: ui-monospace, monospace;
  }
  .scripture-content a {
    color: var(--color-jade);
  }
  .scripture-content a:hover {
    text-decoration: underline;
  }
</style>
`;

fs.writeFileSync(path.join(pagesDir, '01.astro'), getAstroTemplate(1, 'shopping', '01-shopping.md'));
fs.writeFileSync(path.join(pagesDir, '02.astro'), getAstroTemplate(2, 'airport', '02-airport.md'));
fs.writeFileSync(path.join(pagesDir, '03.astro'), getAstroTemplate(3, 'directions', '03-directions.md'));

console.log("Files created successfully.");
