document.addEventListener('DOMContentLoaded', function() {
    // Calculate reading time for all articles on the page
    const articles = document.querySelectorAll('article');
    
    articles.forEach(article => {
        const text = article.textContent || article.innerText;
        const wordCount = text.trim().split(/\s+/).length;
        const readingTime = Math.ceil(wordCount / 200); // 200 words per minute
        
        // Replace READING_TIME placeholder
        const placeholders = article.querySelectorAll('.reading-time');
        placeholders.forEach(el => {
            if (el.textContent.includes('READING_TIME')) {
                el.innerHTML = el.innerHTML.replace('READING_TIME', readingTime);
            }
        });
    });
    
    // Also handle standalone reading time elements (header/footer)
    document.querySelectorAll('.reading-time').forEach(el => {
        if (el.textContent.includes('READING_TIME')) {
            // Find the nearest article to calculate word count
            const article = el.closest('article') || document.querySelector('article');
            if (article) {
                const text = article.textContent || article.innerText;
                const wordCount = text.trim().split(/\s+/).length;
                const readingTime = Math.ceil(wordCount / 200);
                el.innerHTML = el.innerHTML.replace('READING_TIME', readingTime);
            }
        }
    });
});
