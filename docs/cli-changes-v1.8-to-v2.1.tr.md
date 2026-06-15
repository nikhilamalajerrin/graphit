---
layout: default
title: "CLI Değişiklikleri: v1.8'den v2.1'e"
parent: "Turkish (Beta)"
---

# CLI Değişiklikleri: v1.8'den v2.1'e

> **Beta Translation:** This document was translated via Machine Learning and as such may not be 100% accurate. All non-English languages are currently classified as Beta.

## Özet

CLI (`graphit-cli`), üç tema üzerine odaklanmış önemli eklemeler içerir:
**açıklanabilirlik/kaynak**, **gömme erişimi** ve **graf sorgulama**.
İki eski araç kaldırıldı, biri yeniden adlandırıldı ve birkaç mevcut araç
yeni yetenekler kazandı.

--

## Yeni CLI Araçları

### Açıklanabilirlik ve Kaynak

| Komut | Açıklama |
|---------|-------------|
| `gr-list-explain-traces` | Bir koleksiyondaki tüm açıklanabilirlik oturumlarını (GraphRAG ve Agent) listeler, oturum kimliklerini, türü, soru metnini ve zaman damgalarını gösterir. |
| `gr-show-explain-trace` | Bir oturum için tam açıklanabilirlik izini görüntüler. GraphRAG için: Soru, Keşif, Odak, Sentez aşamaları. Agent için: Oturum, Yinelemeler (düşünce/eylem/gözlem), Son Cevap. İz türünü otomatik olarak algılar. `--show-provenance` ile kaynak belgelere kadar kenarları izlemeyi destekler. |
| `gr-show-extraction-provenance` | Bir belge kimliği verildiğinde, kaynak zincirini izler: Belge -> Sayfalar -> Parçalar -> Kenarlar, `prov:wasDerivedFrom` ilişkilerini kullanarak. `--show-content` ve `--max-content` seçeneklerini destekler. |

### Gömme (Embeddings)

| Komut | Açıklama |
|---------|-------------|
| `gr-invoke-embeddings` | Metni, gömme hizmeti aracılığıyla bir vektör gömmesine dönüştürür. Bir veya daha fazla metin girişi alır, vektörleri kayan nokta listeleri olarak döndürür. |
| `gr-invoke-graph-embeddings` | Vektör gömmelerini kullanarak grafik varlıklarını metin benzerliğiyle sorgular. Eşleşen varlıkları benzerlik puanlarıyla döndürür. |
| `gr-invoke-document-embeddings` | Vektör gömmelerini kullanarak belge parçalarını metin benzerliğiyle sorgular. Eşleşen parça kimliklerini benzerlik puanlarıyla döndürür. |
| `gr-invoke-row-embeddings` | Vektör gömmelerini kullanarak dizinlenmiş alanlarda yapılandırılmış veri satırlarını metin benzerliğiyle sorgular. Eşleşen satırları, indeks değerlerini ve puanları döndürür. `--schema-name` gerektirir ve `--index-name`'yi destekler. |

### Graf Sorgulama

| Komut | Açıklama |
|---------|-------------|
| `gr-query-graph` | Desen tabanlı üçlü depolama sorgusu. `gr-show-graph`'in aksine (her şeyi dökerek), bu, herhangi bir konu, yüklem, nesne ve graf kombinasyonuyla seçici sorgular yapmayı sağlar. Değer türlerini otomatik olarak algılar: IRI'lar (`http://...`, `urn:...`, `<...>`), tırnak işaretli üçlüler (`<<s p o>>`) ve literal'lar. |
| `gr-get-document-content` | Belge kimliğine göre kütüphaneden belge içeriğini alır. Dosyaya veya standart çıktıya yazabilir, hem metin hem de ikili içeriği işler. |

--

## Kaldırılan CLI Araçları

| Komut | Notlar |
|---------|-------|
| `gr-load-pdf` | Kaldırıldı. Belge yükleme artık kütüphane/işlem hattı aracılığıyla yapılır. |
| `gr-load-text` | Kaldırıldı. Belge yükleme artık kütüphane/işlem hattı aracılığıyla yapılır. |

--

## Yeniden Adlandırılan CLI Araçları

| Eski Ad | Yeni Ad | Notlar |
|----------|----------|-------|
| `gr-invoke-objects-query` | `gr-invoke-rows-query` | Yapılandırılmış veri için "nesneler" teriminin "satırlar" terimine dönüştürülmesini yansıtır. |

--

## Mevcut Araçlara Yönelik Önemli Değişiklikler

### `gr-invoke-graph-rag`

**Açıklanabilirlik desteği**: Artık, yerleşik kaynak olay gösterimiyle (Question, Grounding/Exploration, Focus, Synthesis) 4 aşamalı bir açıklanabilirlik işlem hattını destekler.
**Akış**: Gerçek zamanlı çıktı için WebSocket akışını kullanır.
**Kaynak takibi**: Seçilen kenarları yeniden yapılandırma ve `prov:wasDerivedFrom` zincirleri aracılığıyla kaynak belgelere kadar izleyebilir.
Tam açıklanabilirlik işlem hattını barındırmak için ~30 satırdan ~760 satıra yükseldi.

### `gr-invoke-document-rag`

**Açıklanabilirlik desteği**: İçerik tabanlı yanıtları (Document RAG) yerleşik kaynak olaylarıyla (Question, Grounding, Exploration, Synthesis aşamaları) akışla gönderen `question_explainable()` modunu ekledi.

### `gr-invoke-agent`

**Açıklanabilirlik desteği**: Ajan yürütülmesi sırasında kaynak olaylarını yerleşik olarak gösteren `question_explainable()` modunu ekledi (Question, Analysis, Conclusion, AgentThought, AgentObservation, AgentAnswer).
Ayrıntılı mod, düşünce/gözlem akışlarını emoji ön ekleriyle gösterir.

### `gr-show-graph`

**Akış modu**: Daha düşük ilk sonuç süresi ve azaltılmış bellek yükü için yapılandırılabilir toplu boyutlarla `triples_query_stream()`'ı kullanır.
**Adlandırılmış grafik desteği**: Yeni `--graph` filtre seçeneği. Adlandırılmış grafikleri tanır:
  Varsayılan grafik (boş): Temel bilgi gerçekleri
  `urn:graph:source`: Çıkarma kaynağı
  `urn:graph:retrieval`: Sorgu zamanı açıklanabilirliği
**Grafik sütununu göster**: Her üçlü için adlandırılmış grafiği görüntülemek için yeni `--show-graph` bayrağı.
**Yapılandırılabilir sınırlar**: Yeni `--limit` ve `--batch-size` seçenekleri.

### `gr-graph-to-turtle`

**RDF-star desteği**: Artık tırnaklı üçlüleri (RDF-star yeniden yapılandırması) işler.
**Akış modu**: Daha düşük ilk işleme süresi için akışı kullanır.
**Tel formatı işleme**: IRIs için `{"t": "i", "i": uri}`, literal'lar için `{"t": "l", "v": value}` ve tırnaklı üçlüler için `{"t": "r", "r": {...}}` kullanan yeni terim tel formatını kullanmak üzere güncellendi.
**Adlandırılmış grafik desteği**: Yeni `--graph` filtre seçeneği.

### `gr-set-tool`

**Yeni araç türü**: Yapılandırılmış veri dizinlerinde semantik arama için `row-embeddings-query`.
**Yeni seçenekler**: Satır gömme sorgu araçlarını yapılandırmak için `--schema-name`, `--index-name`, `--limit`.

### `gr-show-tools`

`schema-name`, `index-name` ve `limit` alanlarıyla yeni `row-embeddings-query` araç türünü görüntüler.

### `gr-load-knowledge`

**İlerleme raporlama**: Her dosya ve toplamda yüklenen üçlü ve varlık bağlamlarının sayısını sayar ve raporlar.
**Terim formatı güncellemesi**: Varlık bağlamları artık eski Değer formatının (`{"v": entity, "e": True}`) yerine yeni Terim formatını (`{"t": "i", "i": uri}`) kullanır.

--

## Uyumluluk Sorunları

**Terminoloji yeniden adlandırması**: `Value` şeması, sistem genelinde `Term` olarak yeniden adlandırıldı (PR #622). Bu, grafik deposuyla etkileşimde bulunan CLI araçları tarafından kullanılan tel formatını etkiler. Yeni format, eski `{"v": ..., "e": ...}` formatının yerini alarak IRIs için `{"t": "i", "i": uri}` ve literal'lar için `{"t": "l", "v": value}` kullanır.
`gr-invoke-objects-query` yeniden adlandırıldı `gr-invoke-rows-query`.
`gr-load-pdf` ve `gr-load-text` kaldırıldı.
