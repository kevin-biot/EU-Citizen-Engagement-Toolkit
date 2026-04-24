# GDPR Controller Establishment Map

Source: [gdpr-controller-establishment-map.csv](/Users/kevinbrown/EU-Citizen-Engagement-Toolkit/data/national-authorities/gdpr-controller-establishment-map.csv:1)

This is a practical clue file for large cross-border GDPR campaigns.

It is **not** a definitive lead-authority register.

Use it when:

- a complaint involves a large platform or multinational controller
- one-stop-shop questions are starting to matter
- you need a first evidence-backed clue about the likely main establishment
- you want to understand why a DPA may be pointing toward Ireland, the Netherlands, or Sweden

Current coverage in this pass: `14` major controllers.

| controller | examples | establishment clue | likely lead DPA | confidence | key caveat |
| --- | --- | --- | --- | --- | --- |
| Meta | Facebook, Instagram, Messenger, Threads | Meta points EEA and UK users to `Meta Platforms Ireland Limited` and the Irish supervisory route in its privacy policy. | [Data Protection Commission](https://www.dataprotection.ie/) (`Ireland`) | `medium` | Product-specific or workplace contexts can still change the analysis. |
| Google | Search, Gmail, Maps, YouTube consumer services | Google's consumer terms say EEA and Switzerland users contract with `Google Ireland Limited`, and that country-version affiliate processes user information. | [Data Protection Commission](https://www.dataprotection.ie/) (`Ireland`) | `medium` | This is a consumer-services establishment clue, not a full controller determination for every product or adtech flow. |
| Microsoft | Microsoft account, Outlook, Bing, consumer cloud services | Microsoft's privacy statement identifies `Microsoft Ireland Operations Limited` for EEA, UK, and Switzerland users where Microsoft is the controller. | [Data Protection Commission](https://www.dataprotection.ie/) (`Ireland`) | `high` | Microsoft often splits controller and processor roles across product families. |
| LinkedIn | LinkedIn profile, feed, messaging, ads | LinkedIn says `LinkedIn Ireland Unlimited Company` is the controller in the Designated Countries. | [Data Protection Commission](https://www.dataprotection.ie/) (`Ireland`) | `high` | Some recruiter or enterprise workflows can sit under different contracts. |
| TikTok | TikTok app, account, recommendations, ads | TikTok's EEA policy names `TikTok Technology Limited` in Ireland and a UK entity as joint controllers. | [Data Protection Commission](https://www.dataprotection.ie/) (`Ireland`) | `medium` | The joint-controller setup means the Irish clue is strong but not universal. |
| X | X social platform, DMs, ads | X says `X Internet Unlimited Company` is the controller for EU, EFTA, and UK users. | [Data Protection Commission](https://www.dataprotection.ie/) (`Ireland`) | `high` | Specific advertiser or business-product disputes can still raise separate questions. |
| Apple | Apple ID, App Store, iCloud, device services | Apple says EEA, UK, and Switzerland personal data is controlled by `Apple Distribution International Limited` in Ireland. | [Data Protection Commission](https://www.dataprotection.ie/) (`Ireland`) | `high` | Apple also uses service-specific privacy pages and partner terms. |
| Spotify | Spotify streaming, account, personalization, ads | Spotify says `Spotify AB` is the data controller. | [Integritetsskyddsmyndigheten](https://www.imy.se/) (`Sweden`) | `high` | Advertising and partner-data disputes can still involve separate actors. |
| Booking.com | Booking.com accommodation booking services | Booking.com says `Booking.com B.V.` in Amsterdam is the controller for the processing described in its privacy statement. | [Autoriteit Persoonsgegevens](https://autoriteitpersoonsgegevens.nl/) (`Netherlands`) | `high` | Hotels and other travel partners can be separate controllers for their own processing. |
| OpenAI | ChatGPT and related consumer services | OpenAI's Rest of World policy identifies `OpenAI Ireland Limited` for EEA, Switzerland, and UK users. | [Data Protection Commission](https://www.dataprotection.ie/) (`Ireland`) | `high` | API, enterprise, and reseller arrangements can allocate roles differently. |
| Netflix | Netflix streaming service, account, recommendations, ads-supported plan | Netflix identifies `Netflix International B.V.` in Amsterdam as the service provider, and says its main establishment within the European Union is in the Netherlands. | [Autoriteit Persoonsgegevens](https://autoriteitpersoonsgegevens.nl/) (`Netherlands`) | `high` | Netflix also lists multiple joint-controller entities for some local-market functions. |
| Airbnb | Airbnb bookings, hosting, platform account, experiences | Airbnb's European terms and outside-US privacy supplement identify `Airbnb Ireland UC` and `Airbnb Global Services Limited` in Dublin for core platform activities outside narrower special cases. | [Data Protection Commission](https://www.dataprotection.ie/) (`Ireland`) | `medium` | Airbnb splits roles across platform, payments, insurance, experiences, and some special booking contexts. |
| PayPal | PayPal consumer account, checkout, peer-to-peer payments | PayPal's EEA user agreement points to `PayPal (Europe) S.à r.l. et Cie, S.C.A.` in Luxembourg as the service provider for EEA users. | [Commission Nationale pour la Protection des Données](http://www.cnpd.lu/) (`Luxembourg`) | `high` | This clue is strongest for core PayPal account and checkout disputes, not every PayPal-adjacent product such as Xoom. |
| Wise | Wise account, card, send-money product | Wise's EEA customer agreement says EEA services are provided by `Wise Europe SA`, a Belgian entity. | [Autorité de la protection des données - Gegevensbeschermingsautoriteit (APD-GBA)](https://www.autoriteprotectiondonnees.be) (`Belgium`) | `medium` | Wise runs multiple entities and specialized products, so this does not automatically answer every Wise-related controller question. |

## How To Use This Safely

- Treat this as a routing clue, not as proof that only one authority matters.
- A complainant can still usually file with the DPA where they live, work, or where the alleged infringement took place.
- The real lead-authority question depends on the controller's main establishment and where relevant processing decisions are taken.
- If the controller family is large and the facts are messy, pair this file with the [GDPR cross-border reference](/Users/kevinbrown/EU-Citizen-Engagement-Toolkit/data/national-authorities/gdpr-cross-border-reference.md:1) and the [one-stop-shop campaign guide](/Users/kevinbrown/EU-Citizen-Engagement-Toolkit/campaigns/gdpr-complaints/one-stop-shop.md:1).

## Why This Exists

In practice, campaign users often hit the same early confusion:

- `Meta` and `TikTok` complaints seem to point to Ireland
- `Booking.com` complaints tend to point to the Netherlands
- `Spotify` complaints tend to point to Sweden

This file makes those patterns legible without pretending that the answer is automatic.

## Official Source Basis

- Meta: [Meta Privacy Policy](https://www.facebook.com/privacy/policy/)
- Google: [Google Terms of Service](https://policies.google.com/terms?hl=en)
- Microsoft: [Microsoft Privacy Statement](https://privacy.microsoft.com/en-us/privacystatement)
- LinkedIn: [LinkedIn Privacy Policy](https://www.linkedin.com/legal/privacy-policy)
- TikTok: [TikTok Privacy Policy for EEA](https://www.tiktok.com/legal/page/eea/privacy-policy/en)
- X: [X Privacy Policy](https://x.com/en/privacy)
- Apple: [Apple Privacy Policy](https://www.apple.com/legal/privacy/en-ww/)
- Spotify: [Spotify Privacy Policy](https://www.spotify.com/ie/legal/privacy-policy/)
- Booking.com: [Booking.com Privacy Statement](https://www.booking.com/content/privacy.en-gb.html)
- OpenAI: [OpenAI Rest of World Privacy Policy](https://openai.com/policies/row-privacy-policy/)
- Netflix: [Netflix Corporate Information](https://help.netflix.com/legal/corpinfo), [Netflix Privacy Statement](https://help.netflix.com/legal/privacy)
- Airbnb: [Airbnb Outside the United States Privacy Supplement](https://www.airbnb.com/help/article/2860)
- PayPal: [PayPal User Agreement](https://www.paypal.com/IE/legalhub/paypal/useragreement-full?locale.x=en-IE), [PayPal Mobile Application License Agreement](https://www.paypal.com/ie/legalhub/paypal/merchmobile-full)
- Wise: [Wise Customer Agreements](https://wise.com/en/legal/terms-and-conditions), [Wise Personal Customer Privacy Notice](https://wise.com/gb/legal/privacy-notice-personal-en)
