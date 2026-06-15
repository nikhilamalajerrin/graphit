---
layout: default
title: "Daha Fazla Yapılandırma CLI Teknik Özellikleri"
parent: "Turkish (Beta)"
---

# Daha Fazla Yapılandırma CLI Teknik Özellikleri

> **Beta Translation:** This document was translated via Machine Learning and as such may not be 100% accurate. All non-English languages are currently classified as Beta.

## Genel Bakış

Bu özellik, GraphIt için gelişmiş komut satırı yapılandırma yeteneklerini tanımlar ve kullanıcıların ayrı yapılandırma öğelerini ayrıntılı CLI komutları aracılığıyla yönetmelerini sağlar. Bu entegrasyon, dört birincil kullanım senaryosunu destekler:

1. **Yapılandırma Öğelerini Listele**: Belirli bir türdeki yapılandırma anahtarlarını görüntüleyin
2. **Yapılandırma Öğesini Al**: Belirli yapılandırma değerlerini alın
3. **Yapılandırma Öğesini Ekle/Güncelle**: Bireysel yapılandırma öğelerini ayarlayın veya güncelleyin
4. **Yapılandırma Öğesini Sil**: Belirli yapılandırma öğelerini kaldırın

## Hedefler

**Ayrıntılı Kontrol**: Toplu işlemler yerine bireysel yapılandırma öğelerinin yönetimini sağlayın
**Türe Dayalı Listeleme**: Kullanıcıların yapılandırma öğelerini türe göre incelemesine izin verin
**Tek Öğeli İşlemler**: Bireysel yapılandırma öğelerinin alınması/eklenmesi/güncellenmesi/silinmesi için komutlar sağlayın
**API Entegrasyonu**: Tüm işlemler için mevcut Config API'sini kullanın
**Tutarlı CLI Modeli**: Kuruluş içi GraphIt CLI kurallarına ve kalıplarına uyun
**Hata Yönetimi**: Geçersiz işlemler için açık hata mesajları sağlayın
**JSON Çıkışı**: Programlı kullanım için yapılandırılmış çıktı desteği sağlayın
**Belgeleme**: Kapsamlı yardım ve kullanım örnekleri ekleyin

## Arka Plan

GraphIt şu anda Config API ve tüm yapılandırmayı görüntüleyen `gr-show-config` adlı tek bir CLI komutu aracılığıyla yapılandırma yönetimini sağlar. Bu, yapılandırmayı görüntülemek için işe yarasa da, ayrıntılı yönetim yetenekleri eksiktir.

Mevcut sınırlamalar şunlardır:
CLI'den yapılandırma öğelerini türe göre listelemenin bir yolu yok
Belirli yapılandırma değerlerini almak için bir CLI komutu yok
Bireysel yapılandırma öğelerini ayarlamak için bir CLI komutu yok
Belirli yapılandırma öğelerini silmek için bir CLI komutu yok

Bu özellik, ayrıntılı yapılandırma yönetimi sağlayan dört yeni CLI komutu ekleyerek bu boşlukları giderir. Bireysel Config API işlemlerini CLI komutları aracılığıyla açığa çıkararak GraphIt şunları yapabilir:
Betik tabanlı yapılandırma yönetimini etkinleştirin
Yapılandırma yapısını türe göre incelemeye izin verin
Hedefli yapılandırma güncellemelerini destekleyin
İnce taneli yapılandırma kontrolü sağlayın

## Teknik Tasarım

### Mimari

Gelişmiş CLI yapılandırması, aşağıdaki teknik bileşenleri gerektirir:

1. **gr-list-config-items**
   Belirtilen bir tür için yapılandırma anahtarlarını listeler
   Config.list(type) API yöntemini çağırır
   Yapılandırma anahtarlarının listesini çıktı olarak verir
   
   Modül: `graphit.cli.list_config_items`

2. **gr-get-config-item**
   Belirli yapılandırma öğesi(ni) alır
   Config.get(keys) API yöntemini çağırır
   Yapılandırma değerlerini JSON formatında çıktı olarak verir

   Modül: `graphit.cli.get_config_item`

3. **gr-put-config-item**
   Bir yapılandırma öğesini ayarlar veya günceller
   Config.put(values) API yöntemini çağırır
   Tür, anahtar ve değer parametrelerini kabul eder

   Modül: `graphit.cli.put_config_item`

4. **gr-delete-config-item**
   Bir yapılandırma öğesini siler
   Config.delete(keys) API yöntemini çağırır
   Tür ve anahtar parametrelerini kabul eder

   Modül: `graphit.cli.delete_config_item`

### Veri Modelleri

#### ConfigKey ve ConfigValue

Bu komutlar, `graphit.api.types`'dan mevcut veri yapılarını kullanır:

```python
@dataclasses.dataclass
class ConfigKey:
    type : str
    key : str

@dataclasses.dataclass
class ConfigValue:
    type : str
    key : str
    value : str
```

Bu yaklaşım şunları sağlar:
CLI ve API'ler arasında tutarlı veri işleme
Tür güvenli yapılandırma işlemleri
Yapılandırılmış girdi/çıktı formatları
Mevcut Config API ile entegrasyon

### CLI Komut Özellikleri

#### gr-list-config-items
```bash
gr-list-config-items --type <config-type> [--format text|json] [--api-url <url>]
```
**Amaç**: Belirli bir tür için tüm yapılandırma anahtarlarını listele.
**API Çağrısı**: `Config.list(type)`
**Çıktı**:
  `text` (varsayılan): Yeni satırlarla ayrılmış yapılandırma anahtarları.
  `json`: Yapılandırma anahtarlarının JSON dizisi.

#### gr-get-config-item
```bash
gr-get-config-item --type <type> --key <key> [--format text|json] [--api-url <url>]
```
**Amaç**: Belirli bir yapılandırma öğesini almak.
**API Çağrısı**: `Config.get([ConfigKey(type, key)])`
**Çıktı**:
  `text` (varsayılan): Ham metin değeri.
  `json`: JSON olarak kodlanmış metin değeri.

#### gr-put-config-item
```bash
gr-put-config-item --type <type> --key <key> --value <value> [--api-url <url>]
gr-put-config-item --type <type> --key <key> --stdin [--api-url <url>]
```
**Amaç**: Yapılandırma öğesini ayarlayın veya güncelleyin.
**API Çağrısı**: `Config.put([ConfigValue(type, key, value)])`
**Giriş Seçenekleri**:
  `--value`: Değer, doğrudan komut satırından sağlanır.
  `--stdin`: Değer, standart girişten okunur.
**Çıktı**: Başarı onayı.

#### gr-delete-config-item
```bash
gr-delete-config-item --type <type> --key <key> [--api-url <url>]
```
**Amaç**: Yapılandırma öğesini silme
**API Çağrısı**: `Config.delete([ConfigKey(type, key)])`
**Çıktı**: Başarı onayı

### Uygulama Detayları

Tüm komutlar, mevcut GraphIt CLI kalıbını izler:
Komut satırı argüman ayrıştırması için `argparse` kullanın
Arka uç iletişimi için `graphit.api.Api`'i içe aktarın ve kullanın
Mevcut CLI komutlarındaki aynı hata işleme kalıplarını izleyin
API uç noktası yapılandırması için standart `--api-url` parametresini destekleyin
Açıklayıcı yardım metni ve kullanım örnekleri sağlayın

#### Çıktı Biçimi İşleme

**Metin Biçimi (Varsayılan)**:
`gr-list-config-items`: Her satırda bir anahtar, düz metin
`gr-get-config-item`: Ham dize değeri, tırnak veya kodlama yok

**JSON Biçimi**:
`gr-list-config-items`: `["key1", "key2", "key3"]` dize dizisi
`gr-get-config-item`: JSON ile kodlanmış dize değeri `"actual string value"`

#### Giriş İşleme

**gr-put-config-item**, iki karşılıklı olarak münhasır giriş yöntemini destekler:
`--value <string>`: Doğrudan komut satırı dize değeri
`--stdin`: Tüm girdiyi yapılandırma değeri olarak standart girdiden okuyun
stdin içeriği ham metin olarak okunur (satır başları, boşluklar vb. korunur)
Dosyalardan, komutlardan veya etkileşimli girdiden boru hattı desteği

## Güvenlik Hususları

**Giriş Doğrulama**: Tüm komut satırı parametreleri, API çağrıları yapılmadan önce doğrulanmalıdır.
**API Kimlik Doğrulama**: Komutlar, mevcut API kimlik doğrulama mekanizmalarını kullanır.
**Yapılandırma Erişimi**: Komutlar, mevcut yapılandırma erişim kontrollerine saygı gösterir.
**Hata Bilgisi**: Hata mesajları, hassas yapılandırma ayrıntılarını ifşa etmemelidir.

## Performans Hususları

**Tek Öğeli İşlemler**: Komutlar, toplu işlem yükünü önlemek için tek tek öğeler için tasarlanmıştır.
**API Verimliliği**: Doğrudan API çağrıları, işleme katmanlarını en aza indirir.
**Ağ Gecikmesi**: Her komut, tek bir API çağrısı yapar ve bu da ağ iletişimini en aza indirir.
**Bellek Kullanımı**: Tek öğeli işlemler için minimum bellek kullanımı.

## Test Stratejisi

**Birim Testleri**: Her CLI komut modülünü bağımsız olarak test edin.
**Entegrasyon Testleri**: CLI komutlarını canlı Config API'ye karşı test edin.
**Hata Yönetimi Testleri**: Geçersiz girişler için uygun hata yönetimini doğrulayın.
**API Uyumluluğu**: Komutların mevcut Config API sürümleriyle çalıştığından emin olun.

## Geçiş Planı

Geçiş gerekli değil - bunlar, mevcut işlevselliği tamamlayan yeni CLI komutlarıdır:
Mevcut `gr-show-config` komutu değişmeden kalır.
Yeni komutlar kademeli olarak eklenebilir.
Mevcut yapılandırma iş akışlarında herhangi bir değişiklik yapılmaz.

## Paketleme ve Dağıtım

Bu komutlar, mevcut `graphit-cli` paketine eklenecektir:

**Paket Konumu**: `graphit-cli/`
**Modül Dosyaları**:
`graphit-cli/graphit/cli/list_config_items.py`
`graphit-cli/graphit/cli/get_config_item.py`
`graphit-cli/graphit/cli/put_config_item.py`
`graphit-cli/graphit/cli/delete_config_item.py`

**Giriş Noktaları**: `graphit-cli/pyproject.toml`'a `[project.scripts]` bölümüne eklendi:
```toml
gr-list-config-items = "graphit.cli.list_config_items:main"
gr-get-config-item = "graphit.cli.get_config_item:main"
gr-put-config-item = "graphit.cli.put_config_item:main"
gr-delete-config-item = "graphit.cli.delete_config_item:main"
```

## Uygulama Görevleri

1. **CLI Modüllerini Oluşturma**: `graphit-cli/graphit/cli/` içinde dört CLI komut modülünü uygulayın.
2. **pyproject.toml'yi Güncelleme**: `graphit-cli/pyproject.toml`'a yeni komut giriş noktaları ekleyin.
3. **Belgeleme**: `docs/cli/` içindeki her komut için CLI belgelerini oluşturun.
4. **Test**: Kapsamlı test kapsamı uygulayın.
5. **Entegrasyon**: Komutların mevcut GraphIt altyapısıyla çalıştığından emin olun.
6. **Paket Oluşturma**: Komutların `pip install graphit-cli` ile düzgün bir şekilde yüklendiğini doğrulayın.

## Kullanım Örnekleri

#### Yapılandırma öğelerini listeleme
```bash
# List prompt keys (text format)
gr-list-config-items --type prompt
template-1
template-2
system-prompt

# List prompt keys (JSON format)  
gr-list-config-items --type prompt --format json
["template-1", "template-2", "system-prompt"]
```

#### Yapılandırma öğesini al
```bash
# Get prompt value (text format)
gr-get-config-item --type prompt --key template-1
You are a helpful assistant. Please respond to: {query}

# Get prompt value (JSON format)
gr-get-config-item --type prompt --key template-1 --format json
"You are a helpful assistant. Please respond to: {query}"
```

#### Yapılandırma öğesini ayarlayın
```bash
# Set from command line
gr-put-config-item --type prompt --key new-template --value "Custom prompt: {input}"

# Set from file via pipe
cat ./prompt-template.txt | gr-put-config-item --type prompt --key complex-template --stdin

# Set from file via redirect
gr-put-config-item --type prompt --key complex-template --stdin < ./prompt-template.txt

# Set from command output
echo "Generated template: {query}" | gr-put-config-item --type prompt --key auto-template --stdin
```

#### Yapılandırma öğesini sil
```bash
gr-delete-config-item --type prompt --key old-template
```

## Açık Sorular

Komutlar, tek öğelerin yanı sıra toplu işlemleri (çoklu anahtarlar) desteklemeli mi?
Başarı onayları için hangi çıktı formatı kullanılmalıdır?
Konfigürasyon türleri kullanıcılar tarafından nasıl belgelenmeli/keşfedilmelidir?

## Referanslar

Mevcut Konfigürasyon API'si: `graphit/api/config.py`
CLI kalıpları: `graphit-cli/graphit/cli/show_config.py`
Veri türleri: `graphit/api/types.py`
