# WVS catalog execution matrix

Checked from the saved OpenRouter catalog on 2026-09-16. Protocol IDs hash all rendered WVS prompts and settings. `response_format` is only requested where the catalog advertises it. A mandatory model uses its least listed effort. Entries with mandatory reasoning but no supported-effort list are excluded rather than guessing a setting. These are candidate runs, not completed points.

| exact ID | catalog name | created UTC | input USD/M | output USD/M | reasoning | schema | protocol ID |
|---|---|---:|---:|---:|---|---|---|
| `anthropic/claude-fable-5.1` | Anthropic: Claude Fable 5.1 | 2026-09-01 | 10 | 50 | mandatory low | True | `4230ccaa1e160c793a906aef6b786d735d9fdbf71c3333691b0eba17dcf33928` |
| `deepseek/deepseek-v4.1-flash` | DeepSeek: DeepSeek V4.1 Flash | 2026-09-10 | 0.15 | 0.6 | disabled | True | `8c27d32cd851de5f217cb354b15dc270cc6f4ec2d02fb15dbb20fde0790c3571` |
| `google/gemini-3.7-flash` | Google: Gemini 3.7 Flash | 2026-08-13 | 0.75 | 3.75 | mandatory low | True | `cd5db529649a179032180cecafe4fd98aff124ee3654f7d60996de704e2b63ef` |
| `meta/muse-spark-1.3` | Meta: Muse Spark 1.3 | 2026-09-02 | 1.25 | 4.25 | mandatory minimal | True | `b4d16afd9ddaf199d12f114c09c100c421d615cbaffed12cbb0f89d3d13d635f` |
| `moonshotai/kimi-k3` | MoonshotAI: Kimi K3 | 2026-07-16 | 2.64814 | 13.2827 | disabled | True | `0043a43d1a2188f7c728ccda08eee7b062232366d8a4e912c72bdc938e37fe44` |
| `openai/gpt-5.6-sol` | OpenAI: GPT-5.6 Sol | 2026-07-09 | 2 | 10 | disabled | True | `1a70f47789af20900f2799992b09e83af9490be6579098a6178d613d5ba7856c` |
| `openai/gpt-6-astra` | OpenAI: GPT-6 Astra | 2026-09-04 | 10 | 50 | mandatory low | True | `95bb4d3939e9937823357b5cd87adb1a6640cc5b04e0841dfec03095331a5e44` |
| `qwen/qwen-2.5-72b-instruct` | Qwen2.5 72B Instruct | 2024-09-19 | 0.36 | 0.4 | none advertised | True | `9c1d40b30945565e488b212177e40c29f730c2e96d4b07d09cbc135ba75a81f0` |
| `qwen/qwen-2.5-7b-instruct` | Qwen: Qwen2.5 7B Instruct | 2024-10-16 | 0.1 | 0.2 | none advertised | True | `66ad076e1a37493e4d3db982a0220048e520103459cefc709bc8f09f3fef6c9a` |
| `qwen/qwen-2.5-coder-32b-instruct` | Qwen2.5 Coder 32B Instruct | 2024-11-11 | 0.66 | 1 | none advertised | False | `c10652513faf6e0ff56b5fb1f7e395a4e72aa5971817e3d183bca4aa9d3ac70f` |
| `qwen/qwen-plus` | Qwen: Qwen-Plus | 2025-02-01 | 0.26 | 0.78 | none advertised | True | `88ba5af838eda5d298b312553d7c941e72a37cbf28890cdb9d8436b5f40e7cfe` |
| `qwen/qwen-plus-2025-07-28` | Qwen: Qwen Plus 0728 | 2025-09-08 | 0.26 | 0.78 | none advertised | True | `ac52652ff1f09e1f1972a8b751e1b1deca329cb555df54755aada79791bed940` |
| `qwen/qwen2.5-vl-72b-instruct` | Qwen: Qwen2.5 VL 72B Instruct | 2025-02-01 | 0.8 | 1 | none advertised | True | `02d386b067d55e0639d33db8b6f1e5c708c30acbada3125dcbabde47dc90edcf` |
| `qwen/qwen3-14b` | Qwen: Qwen3 14B | 2025-04-28 | 0.12 | 0.24 | disabled | True | `49ae9f7a09090534a15fac734c2611c445a17139cad6c5684fa0581722f3fd70` |
| `qwen/qwen3-235b-a22b` | Qwen: Qwen3 235B A22B | 2025-04-28 | 0.455 | 1.82 | disabled | True | `842298c634ec0f57848b605f67fca161631a852a68192cae1a5377b1d9f31566` |
| `qwen/qwen3-235b-a22b-2507` | Qwen: Qwen3 235B A22B Instruct 2507 | 2025-07-21 | 0.0875 | 0.35 | none advertised | True | `dc09c3fe433c95591b336b279603c546152daf6534d90699323b3bcde754f5bf` |
| `qwen/qwen3-235b-a22b-thinking-2507` | Qwen: Qwen3 235B A22B Thinking 2507 | 2025-07-25 | 0.23 | 2.3 | mandatory effort unknown | True | `not runnable` |
| `qwen/qwen3-30b-a3b` | Qwen: Qwen3 30B A3B | 2025-04-28 | 0.12 | 0.5 | disabled | True | `8700e79d3eccf358a0de1029f7b40e2db339bb6d11403b8e69cb7a66a7b0c668` |
| `qwen/qwen3-30b-a3b-instruct-2507` | Qwen: Qwen3 30B A3B Instruct 2507 | 2025-07-29 | 0.04815 | 0.19305 | none advertised | True | `88ed922f271a76721ad18f0b7bb9693a48377e2507d02a4b78fa08b451972d83` |
| `qwen/qwen3-30b-a3b-thinking-2507` | Qwen: Qwen3 30B A3B Thinking 2507 | 2025-08-28 | 0.2 | 2.4 | mandatory effort unknown | True | `not runnable` |
| `qwen/qwen3-32b` | Qwen: Qwen3 32B | 2025-04-28 | 0.08 | 0.28 | disabled | True | `580a5840948209ecb177dc6fdaf36e265a32ccfe223d791eb3235fea9269f27e` |
| `qwen/qwen3-8b` | Qwen: Qwen3 8B | 2025-04-28 | 0.117 | 0.455 | disabled | True | `589e10fa7924ecf8f88650d6587ff37c440f47c6c4cc4325c7009ef8d4eeb4ec` |
| `qwen/qwen3-coder` | Qwen: Qwen3 Coder 480B A35B | 2025-07-23 | 0.3 | 1 | none advertised | True | `304db4b1aa6c80d734f802749c75143feddfcdb740c4131385e927148ba7d05b` |
| `qwen/qwen3-coder-30b-a3b-instruct` | Qwen: Qwen3 Coder 30B A3B Instruct | 2025-07-31 | 0.07 | 0.28 | none advertised | True | `39659697ca3437f62be4fb8e129e6b3902a91b5acac3243ca914dfc917dd563b` |
| `qwen/qwen3-coder-flash` | Qwen: Qwen3 Coder Flash | 2025-09-17 | 0.195 | 0.975 | none advertised | True | `d7e09ed951a3e1310a5e6bf09ac6aab40a68d37524c6bc20c16c0206fd08a532` |
| `qwen/qwen3-coder-next` | Qwen: Qwen3 Coder Next | 2026-02-04 | 0.12 | 0.8 | none advertised | True | `57bed80fd5b94157effe68fe998c7c12612fea210c1371dbf230097a7e8e0717` |
| `qwen/qwen3-coder-plus` | Qwen: Qwen3 Coder Plus | 2025-09-23 | 0.65 | 3.25 | none advertised | True | `182a7e88869698133f1175f18e53e7f6f2f056739559d325b211bd065235a71c` |
| `qwen/qwen3-max` | Qwen: Qwen3 Max | 2025-09-23 | 0.78 | 3.9 | none advertised | True | `fa57e897f1e8246a77fddbb7079541ba14ba0913237434ff6a4096759172bab7` |
| `qwen/qwen3-max-thinking` | Qwen: Qwen3 Max Thinking | 2026-02-09 | 0.78 | 3.9 | disabled | True | `bca0745bdc1554718d57891098f366214f05e9e896007a916d14a06efa33471a` |
| `qwen/qwen3-next-80b-a3b-instruct` | Qwen: Qwen3 Next 80B A3B Instruct | 2025-09-11 | 0.09 | 1.1 | none advertised | True | `9d8a5189c078672eb884784938b183944fb161d0e716e2c44722540b17603e34` |
| `qwen/qwen3-next-80b-a3b-thinking` | Qwen: Qwen3 Next 80B A3B Thinking | 2025-09-11 | 0.15 | 1.2 | mandatory effort unknown | True | `not runnable` |
| `qwen/qwen3-vl-235b-a22b-instruct` | Qwen: Qwen3 VL 235B A22B Instruct | 2025-09-23 | 0.21 | 1.9 | none advertised | True | `61ab1adae3781ca3893328a845d4d517daa5fb47e07ea189da1df45388f62d42` |
| `qwen/qwen3-vl-235b-a22b-thinking` | Qwen: Qwen3 VL 235B A22B Thinking | 2025-09-23 | 0.4 | 4 | mandatory effort unknown | True | `not runnable` |
| `qwen/qwen3-vl-30b-a3b-instruct` | Qwen: Qwen3 VL 30B A3B Instruct | 2025-10-06 | 0.15 | 0.6 | none advertised | True | `0a798666aeed20785b4661c8c2fe4a6fc6853796bc2f3c45133863469e5b3f82` |
| `qwen/qwen3-vl-30b-a3b-thinking` | Qwen: Qwen3 VL 30B A3B Thinking | 2025-10-06 | 0.2 | 2.4 | mandatory effort unknown | True | `not runnable` |
| `qwen/qwen3-vl-32b-instruct` | Qwen: Qwen3 VL 32B Instruct | 2025-10-23 | 0.104 | 0.416 | none advertised | True | `43ddc43fb5a29c7fbf21c8f32b42a909c2118feb9255959ecaeab7dadb1f3dde` |
| `qwen/qwen3-vl-8b-instruct` | Qwen: Qwen3 VL 8B Instruct | 2025-10-14 | 0.117 | 0.455 | none advertised | True | `1d7f4015decbcbe955adb79817b970981ca1d3165ed121b458b213ba1060f675` |
| `qwen/qwen3-vl-8b-thinking` | Qwen: Qwen3 VL 8B Thinking | 2025-10-14 | 0.18 | 2.1 | mandatory effort unknown | True | `not runnable` |
| `qwen/qwen3.5-122b-a10b` | Qwen: Qwen3.5-122B-A10B | 2026-02-25 | 0.26 | 2.08 | disabled | True | `e0a9daef251d975c5e805e159f3813dd0c55b3f0919876b828e572b0530bea88` |
| `qwen/qwen3.5-27b` | Qwen: Qwen3.5-27B | 2026-02-25 | 0.195 | 1.56 | disabled | True | `7058adf367d238c6c92e1b83ae71f6556362e9fc7a243297b6fc65e54e2c2886` |
| `qwen/qwen3.5-35b-a3b` | Qwen: Qwen3.5-35B-A3B | 2026-02-25 | 0.1625 | 1.3 | disabled | True | `7ee20ca2b88f69dd06b9de3018deea4cb7a418e3119e17862cd0b32146daae1a` |
| `qwen/qwen3.5-397b-a17b` | Qwen: Qwen3.5 397B A17B | 2026-02-16 | 0.55 | 3.5 | disabled | True | `921707cb0d3db143e948e9d78cd8191f4ee720eaf56b6934e2d13d9ce9e3382f` |
| `qwen/qwen3.5-9b` | Qwen: Qwen3.5-9B | 2026-03-10 | 0.1 | 0.15 | disabled | True | `3016d2c1ab8d8f88f01723d2d695be996c7f1fdcd442a51cfbb6c7b7110a25e9` |
| `qwen/qwen3.5-flash-02-23` | Qwen: Qwen3.5-Flash | 2026-02-25 | 0.065 | 0.26 | disabled | True | `c946b6990be1e8b0b908a2f5fbb18097b83aa5bc76370127336fe989836b259f` |
| `qwen/qwen3.5-plus-02-15` | Qwen: Qwen3.5 Plus 2026-02-15 | 2026-02-16 | 0.26 | 1.56 | disabled | True | `74e3649a6961000bab284e801fe811d5c8fc4cf1db15af52bb10959f5a5a37c1` |
| `qwen/qwen3.5-plus-20260420` | Qwen: Qwen3.5 Plus 2026-04-20 | 2026-04-27 | 0.3 | 1.8 | disabled | True | `6d6ce30e9fbc5fdb07229b0a08e067d77511857069a4e572613d3e48b7c8b261` |
| `qwen/qwen3.6-27b` | Qwen: Qwen3.6 27B | 2026-04-27 | 0.3 | 2 | disabled | True | `abf45a27f4bafad0eb264aac33b1e49e9d0404e141966954d0707930d56665e3` |
| `qwen/qwen3.6-35b-a3b` | Qwen: Qwen3.6 35B A3B | 2026-04-27 | 0.1 | 0.9 | disabled | True | `b35b916c22649e91ded175aede34f3937a16f42a354f7abab01a17bf2b0dfc97` |
| `qwen/qwen3.6-flash` | Qwen: Qwen3.6 Flash | 2026-04-27 | 0.1875 | 1.125 | disabled | True | `fa37fc90604e5032183ec460bcc2632507566c3be3e9085f61a6ca85582b7d47` |
| `qwen/qwen3.6-max-preview` | Qwen: Qwen3.6 Max Preview | 2026-04-27 | 1.027 | 6.162 | disabled | True | `fa9ff591d389ad2d8a4b7e3fc1410ed588508fe286430c06a941180b0590422b` |
| `qwen/qwen3.6-plus` | Qwen: Qwen3.6 Plus | 2026-04-02 | 0.325 | 1.95 | disabled | True | `96d86b64bf7ceff8eed0daff1aa0396ee69609b5867942a7c2c9d33093f03c9d` |
| `qwen/qwen3.7-flash` | Qwen: Qwen3.7 Flash | 2026-07-27 | 0.03 | 0.13 | disabled | True | `82875b6ee164d0d980eba738bf05f69959234567b91f9cfd01fcabca0bd70dac` |
| `qwen/qwen3.7-max` | Qwen: Qwen3.7 Max | 2026-05-21 | 1.475 | 4.425 | disabled | True | `1c31668055e399de28805046bc08075035efbad0cdb1ff7d8926841a282e07a5` |
| `qwen/qwen3.7-plus` | Qwen: Qwen3.7 Plus | 2026-06-03 | 0.32 | 1.28 | disabled | True | `f095e0d2dbafdb91b51be3d0b3bd5a597730c8e3c397e0461023c87e924d92f8` |
| `qwen/qwen3.8-2.4t-a95b` | Qwen: Qwen3.8 2.4T A95B | 2026-08-12 | 2 | 6 | mandatory low | True | `b6452714bedbbbca3b241939aee504828d55376eed879036f1014c98af07fb14` |
| `qwen/qwen3.8-27b` | Qwen: Qwen3.8 27B | 2026-08-14 | 0.214 | 2.55 | disabled | True | `ed8190c48b2a3778bba8afff7381bb9f1578211b5e8f750d21321b62617c82c3` |
| `qwen/qwen3.8-flash` | Qwen: Qwen3.8 Flash | 2026-08-26 | 0.15 | 0.47 | disabled | True | `3443c17ae66d3fb529a058128b662024c4bc0601394e614bb693b388ec4c988b` |
| `qwen/qwen3.8-max-0902` | Qwen: Qwen3.8 Max (0902) | 2026-09-03 | 2 | 6 | mandatory minimal | True | `f7b53c82a39132f32b6c2beeafacc09db6b360fd9f46a5be0122b2b8a1889653` |
| `thinkingmachines/inkling` | Thinking Machines: Inkling | 2026-07-17 | 1 | 4.05 | disabled | False | `67a70b1b03ba85be79dc122cc888a080fde239205624135a9147168e7e77293d` |
| `x-ai/grok-4.5` | SpaceXAI: Grok 4.5 | 2026-07-08 | 2 | 6 | mandatory low | True | `721da5868b28958d481b18b9afc4ae36db3c2e0235ab0e3ae9a5c2210375d9cf` |
| `z-ai/glm-5.3` | Z.ai: GLM 5.3 | 2026-08-18 | 1.4 | 4.4 | mandatory low | True | `d81f7e66b3c4c720f8dd80768d3dfc25de6edeaf6a352cfed40e961f21fcfa22` |
| `z-ai/glm-5.3-flash` | Z.ai: GLM 5.3 Flash | 2026-08-26 | 0.09 | 0.3 | mandatory low | True | `fdf70c2d5768c4283a40342f78d82a9ebf8326db3b8c7a156a0a1d8da58b240b` |

The initial Qwen 3.7 Flash diagnostic used reasoning on and is excluded. The two corrected-attempt protocol IDs are in the request ledger. -- PI[gpt-5.6-terra]
