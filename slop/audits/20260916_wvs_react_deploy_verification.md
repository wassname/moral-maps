# React WVS deployment verification

Observed after deploy of `f657321`:

- public page: `https://wassname.github.io/moral-maps/wvs/react/`
- public asset reference: `./assets/index-CCNzz5z-.js`
- local and public JavaScript SHA-256: `8297b5c03db01b5d49610c0d39ea877abd0cd87e1c01b0372498232c26eaa03e`
- local and public `wvs_map_data.json` SHA-256: `08dc2a5681eac7305f6c75481fcceebf9a103fad86405c2b662119986910b518`

The deployed asset and shared data bytes therefore matched the local production build at this check. Local React UAT used production build output and browser default/Qwen-hidden captures; it checked 64 models, 90 countries, four zones, 13 latest labels, and the oriented axis labels. -- PI[gpt-5.6-terra]
