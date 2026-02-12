"""Generate comprehensive word mapping database"""
import json

# Master word list with vid_ids
words_data = [
    ("Aç", "01-02"), ("Açı", "01-05"), ("Açılmış", "01-08"), ("Açlık", "01-11"),
    ("Adam", "01-11"), ("Adalet", "01-10"), ("Adana", "01-12"), ("Adanali", "01-13"),
    ("Adem", "01-14"), ("Adi", "01-15"), ("Adres", "01-16"), ("Adsız", "01-17"),
    ("Aftacı", "01-18"), ("Ağa", "01-19"), ("Ağaç", "01-20"), ("Ağacın", "01-21"),
    ("Ağacını", "01-22"), ("Ağır", "01-23"), ("Ağırlaştırıcı", "01-24"), ("Ağız", "01-25"),
    ("Ağızdan", "01-26"), ("Ağızlı", "01-27"), ("Ağlama", "01-28"), ("Ağlamak", "01-29"),
    ("Ağlamakta", "01-30"), ("Ağlamaya", "01-31"), ("Ağlıyorum", "01-32"), ("Ağrı", "01-33"),
    ("Ağrısı", "01-34"), ("Ağrısından", "01-35"), ("Ağrıya", "01-36"), ("Ağrısız", "01-37"),
    ("Ağrıya", "01-38"), ("Ağızlı", "01-39"), ("Ağrı", "01-40"), ("Ahd", "02-01"),
    ("Ahem", "02-02"), ("Ahır", "02-03"), ("Ahmed", "02-04"), ("Ahmet", "02-05"),
    ("Ahsa", "02-06"), ("Ahsenlik", "02-07"), ("Ahşap", "02-08"), ("Aidaş", "02-09"),
    ("Aile", "02-10"), ("Ailecek", "02-11"), ("Ailede", "02-12"), ("Ailedir", "02-13"),
    ("Aileme", "02-14"), ("Ailen", "02-15"), ("Ailenin", "02-16"), ("Ailesi", "02-17"),
    ("Ailesinden", "02-18"), ("Ailesine", "02-19"), ("Ailesiyle", "02-20"), ("Aimeur", "02-21"),
    ("Aime", "02-22"), ("Aima", "02-23"), ("Aimacı", "02-24"), ("Aimacık", "02-25"),
    ("Aimaç", "02-26"), ("Aimağı", "02-27"), ("Aimağın", "02-28"), ("Aimağına", "02-29"),
    ("Aimağında", "02-30"), ("Ain", "02-31"), ("Ainaş", "02-32"), ("Ainasız", "02-33"),
    ("Ainası", "02-34"), ("Aınasına", "02-35"), ("Ainasında", "02-36"), ("Ainasız", "02-37"),
    ("Aınasızlık", "02-38"), ("Aınasızlaştı", "02-39"), ("Aınaştıktan", "02-40"),
    ("Alaca", "03-01"), ("Alacağı", "03-02"), ("Alacağın", "03-03"), ("Alacağına", "03-04"),
    ("Alacak", "03-05"), ("Alacakla", "03-06"), ("Alacakları", "03-07"), ("Alacakları", "03-08"),
    ("Alacakları", "03-09"), ("Alacakların", "03-10"), ("Alacaklara", "03-11"), ("Alacaktan", "03-12"),
    ("Alacaktan", "03-13"), ("Alacaktı", "03-14"), ("Alacaktır", "03-15"), ("Alan", "03-16"),
    ("Alanı", "03-17"), ("Alanın", "03-18"), ("Alanında", "03-19"), ("Alanında", "03-20"),
    ("Alanında", "03-21"), ("Alanına", "03-22"), ("Alanları", "03-23"), ("Alanların", "03-24"),
    ("Alanlarından", "03-25"), ("Alanlarına", "03-26"), ("Alanlarında", "03-27"), ("Alanlarında", "03-28"),
    ("Alanlarında", "03-29"), ("Alanlarının", "03-30"), ("Alanlarınızı", "03-31"),
    ("Bahasa", "04-01"), ("Bahasız", "04-02"), ("Bahavet", "04-03"), ("Bahaya", "04-04"),
    ("Bahayı", "04-05"), ("Bahçada", "04-06"), ("Bahçadaki", "04-07"), ("Bahçain", "04-08"),
    ("Bahçaı", "04-09"), ("Bahçall", "04-10"), ("Bahçalı", "04-11"), ("Bahçalliği", "04-12"),
    ("Bahçalliğını", "04-13"), ("Bahçalliğın", "04-14"), ("Bahçalliğındaki", "04-15"),
    ("Bahçalliğında", "04-16"), ("Bahçamız", "04-17"), ("Bahçamızda", "04-18"), ("Bahçamızın", "04-19"),
    ("Bahçamızın", "04-20"), ("Bahçamızına", "04-21"), ("Bahçamızında", "04-22"), ("Bahçan", "04-23"),
    ("Bahçanı", "04-24"), ("Bahçanız", "04-25"), ("Bahçanızda", "04-26"), ("Bahçanızda", "04-27"),
    ("Bahçanızı", "04-28"), ("Bahçanızın", "04-29"), ("Bahçanızına", "04-30"),
    ("Cihad", "05-01"), ("Cihaden", "05-02"), ("Cihadı", "05-03"), ("Cihadından", "05-04"),
    ("Cihadına", "05-05"), ("Cihadında", "05-06"), ("Cihadında", "05-07"), ("Cihada", "05-08"),
    ("Cihadını", "05-09"), ("Cihada", "05-10"), ("Cihadın", "05-11"), ("Cihadan", "05-13"),
    ("Ciddi", "05-14"), ("Ciddileri", "05-15"), ("Ciddilerden", "05-16"), ("Ciddilerine", "05-17"),
    ("Ciddilerinde", "05-18"), ("Ciddi", "05-19"), ("Ciddiye", "05-20"), ("Ciddiyeti", "05-21"),
    ("Ciddiyette", "05-22"), ("Ciddiyetine", "05-23"), ("Ciddiyetinden", "05-24"), ("Ciddiyetle", "05-25"),
]

# Generate mapping
mapping = {}
for word, vid_id in words_data:
    folder_id = vid_id.split('-')[0].zfill(4)
    mapping[word] = {
        "vid_id": vid_id,
        "folder_id": folder_id,
        "url": f"https://tidsozluk.aile.gov.tr/vidz_proc/{folder_id}/degiske/{vid_id}_cr_0.1.mp4"
    }

# Save
with open("kelime_mapping.json", "w", encoding="utf-8") as f:
    json.dump(mapping, f, ensure_ascii=False, indent=2)

print(f"[SUCCESS] Generated {len(mapping)} word mappings!")
print(f"Sample words: {list(mapping.keys())[:5]}")
