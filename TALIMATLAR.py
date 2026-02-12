"""
Tüm TID Kelimelerini Çıkarmak için Talimatlar:

1. listele.py'i çalıştırın:
   python listele.py

2. Tarayıcı açılacak. F12 tuşuna basıp Console sekmesine gidin.

3. Aşağıdaki kodu kopyalayıp yapıştırın ve Enter'a basın:

---

var words = [];
// Currently visible words - this gets links from the current page
document.querySelectorAll('a').forEach(function(link) {
    var href = link.getAttribute('href');
    if (href && href.startsWith('/tr/') && !href.includes('.html') && link.textContent.trim()) {
        var word = href.split('/').filter(s => s)[1];
        if (word && word !== 'Alfabetik' && word !== 'Arama') {
            words.push(word);
        }
    }
});

// Remove duplicates
words = [...new Set(words)];

// Convert to JSON format suitable for our scraper
var mapping = {};
words.forEach(function(word) {
    mapping[word] = { "word": word };
});

console.log(JSON.stringify(mapping, null, 2));

---

4. Çıktıyı kopyalayıp aşağıya yapıştırın
5. Sonra kelime_mapping.json dosyasını elle düzenleyin veya
   Python script'ini çalıştırın: python optimize_scraper.py

"""

print(__doc__)
