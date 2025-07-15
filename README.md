# AgenticCore

![AgenticCore](media/logo.png)

World's first agentic operating system.

# Contents

- [About](#about)
- [Features](#features)
- [Installation](#installation)
- [Contents](#repository-contents)
- [Usage](#usage)
- [Development Process](#development-process)
- [License](#license)
- [Contact](#contact)
- [Support](#support)

# About
AgenticCore is world's first agentic operating system which can do tasks for you. It has 2 versions: Local and Gemini API. Local uses a custom build of Llama.cpp for Tiny Core while Gemini API version uses Google's Gemini 2.0 Flash API. 

Its capable of generating bash scripts and you can run it with just a click of a button.
Still being in Alpha release, AgenticCore doesnt work flawless for now. We can make it "perfect" together!

# Features
## Local Version
- Being able to choose your own .GGUF AI model
- Being able to change the model by your use-cases anytime.
- No internet connection required.
- Agentic.

## Gemini API Version
- Slightly ligther than Local Version.
- Works faster on old machines.
- Smarter compared to small local models.
- Agentic.

# Installation
**NOTE:** Unfortunately, AgenticCore *currently* doesnt support UEFI.

## Real Device
1. Download the latest release of your desired version from [AgenticCore Website](https://agentic-core.web.app)
2. Flash it to a USB Drive using tools like [Rufus](https://rufus.ie/), [Balena Etcher](https://etcher.balena.io/) etc.
3. Boot it from BIOS menu.
4. For Local version, you can load your .GGUF model from another USB flash and use AgenticCore!
5. For Gemini API version, you can connect to wifi using WiFi program in the dock at top-right and use AgenticCore!

## Virtual Machine
1. Download the latest release of your desired version from [AgenticCore Website](https://agentic-core.web.app)
2. Create a virtual machine in your desired VM application. (OS type: Other Linux (64 bit))
3. Boot your VM.
4. For Local version, you can load your .GGUF model using shared folders function of your VM application.
5. For Gemini API version:
-  If you have NAT option enabled, it should already be connected to internet. You can use AgenticCore directly!
- If you are using bridged adapters, you can connect to wifi using WiFi program in the dock at top-right and use AgenticCore!

# Usage
Using AgenticCore is simple!
Some of the things you need to know:
- Use the dock at top-right to launch applications.
- Use the app called "Agent" in dock to use agent.
- Just ask AI what to do.
- When AI generates a script, you can always reveal the code and inspect the code or run it right away by just pressing the "Run" button.

# Repository Contents
[scripts/main.py](./scripts/main.py "scripts/main.py") -> "Agent" Program of **Local Version!**

[scripts/bootlocal.sh](./scripts/bootlocal.sh "scripts/bootlocal.sh") -> Creates required files for wbar configuration.

[tc-llamacpp/llama-server](tc-llamacpp/llama-server "tc-llamacpp/llama-server") -> The custom build of portable llama-server for Tiny Core, being used by "Agent" app of local version.

Other files / Explanations will be released soon!

# Development Process
- In early 2025, i had this idea, AI-implemented operating systems. I thought there are already some prototypes of this, because it was a cool idea for me. After a quick research, i realised that there is no agentic operating system ever released. I wanted to instantly start this project, but as a 13 year-old student, this year i had a big final exam and working to that. So i didnt be able to.

- In early this summer (01.07.2025), since my exam was over, i checked again, thought some people or companies made a demo of this already. But no, there were still no agentic operating systems in the world!

- In 02.07.2025, i started to work on it. I firstly developed a simple UI for Agent app using Python and Tkinter, since tkinter is light and enough for this project. Made a simple chatbot that uses Gemini API but doesnt have the "agentic" functions yet.

- In 03.07.2025, i implemented basic "agentic" functions using some system prompts and special formats. We were able to see and run the code it generates!

- In 04.07.2025, i did some bugfixes to "Agent" script and booted Tiny Core on a computer to begin the development of AgenticCore itself. I started by downloading the wifi.tcz with its dependencies on my Arch Linux partition using [FetchExt.sh tool](https://forum.tinycorelinux.net/index.php/topic,23034.0.html "FetchExt.sh tool"). Then i succesfully connected to internet and installed python3.9, python3.9-setuptools and pip to my system like this:
`python3 -m ensurepip --default-pip` - This currently installs an older version of pip. So:
`python3 -m pip install --upgrade pip` to update it.

- In 05.07.2025, i have installed google-genai and couple of other dependencies of current "Agent" Python program. To make it portable, i have used `--target` flag of pip. I planned the "universal" file paths for AgenticCore. Packages were going to be in `/ace/` which stands for AgenticCore Extensions. Im also planning to develop and release ACE extension manager as an alternative of TCE as well in next versions! Anyways, i ran the program and debugged it a little bit. It was working. I have created the first version which only had the program inside (for Gemini API version) using `ezremaster` tool and first version of AgenticCore was actually done! (16-1-1)

- In 06.07.2025, i have designed the logo and did some experiments about `wbar` and wallpaper configuration. We can say these were the "last touches". Current version uses [bootlocal.sh](scripts/bootlocal.sh "bootlocal.sh") to create custom wallpaper and wbar config at startup. But 16-1-2 used manually created appconf file in `/home/tc/.X.d` which executes scripts inside of it. So this day, i have built 16-1-2 first and a little improved version of it, 16-1-3. It have gained its current look!

- In 07.07.2025, i found another bug about Agent program and wbar configuration. So i fixed them as well and created the 16-1-4 version, first public release of AgenticCore! In the same day, i created the basic design of AgenticCore website and released Gemini API version 16-1-4!

- In 08.07.2025, i thought making a local version of AgenticCore would be cool, but only planned it in my mind. Other than that, i gave a break :)

- In 09.07.2025, i tried to install llama-cpp-python, installed all the dependencies but i think there were some conflicts with the system, because i debugged for hours but didnt be able to install it. So, i tried building llama.cpp itself. Of course, intended way to build it didnt work. I tried adding `-DLLAMA_STATIC=ON` flag but turns out its deprecated. I tried my chance by `-DCMAKE_EXE_LINKER_FLAGS="-static"` but it gave segmentation fault's so it was broken. I git checkout'd to older versions and tried `-DLLAMA_STATIC=ON` again but when i check the build with `ldd llama-cli` it was showing that its actually still dynamic! After few more hours of trying, i realised its portable even when its dynamic. So my last flags were `-DLLAMA_CURL=OFF` (because we dont need to gather models from hugging face directly in AgenticCore), `-DBUILD_SHARED_LIBS=OFF` (just in case) and `-DCMAKE_BUILD_TYPE=Release`. At the end of the day, i finally have built Llama.cpp specifically for TinyCorePure64!

- In 09.07.2025, i have tried to find a way to integrate the `llama-cli` with python, because as i said, we couldnt use llama-cpp-python. This is lighter and working! So i tried to use some methods i found in [here](https://github.com/ggml-org/llama.cpp/discussions/777 "here") but none of them worked. So i "mixed" some of them and `./llama-cli -m model.gguf -p "Hi" --no-display-prompt 2> /dev/null` was working. But there was an issue: it was waiting for the user input after AI response. So program wasnt finishing. I tried to develop some bash programs which kills the process after no output for 2 seconds etc. to get the raw output, but It wasnt a reliable way to do this. So i planned to use `llama-server` and used `requests` package to get responses from locally-hosted AI.

- In 10.07.2025, i made what i have planned, edited the "Agent" script lots of times, debugged for hours and it was finally working with AI models locally using `llama-server` to host it on localhost.

- In 11.07.2025, i tried the `llama-server` method's portability using simple remasters. It was working!

- In 12.07.2025, i rested :)

- In 13.07.2025, i have created the first "finished" local version as well! But it took a couple of tries, so i built it several times this day. Finally, it was finished!

- In 14,07.2025, i released the AgenticCore's first local version as well! Then, did some updates to AgenticCore Website, including forums. Note: I got help from AI to make some parts of the website and forum section, because im not mainly a web developer. Other than that, AI is not used in the development of AgenticCore!

- In 15.07.2025, i posted about AgenticCore on reddit. It got deleted from 2 subreddits in just a hour due "too much reports". I dont know why :/

# License
AgenticCore is licensed under the Apache License 2.0.
See the [LICENSE](./LICENSE) file for details.

# Contact
You can use the [contact section of AgenticCore website](https://agentic-core.web.app/index.html#contact "contact section of AgenticCore website") or just mail at [tachion.software@gmail.com](mailto:tachion.software@gmail.com?subject=AgenticCore "tachion.software@gmail.com") to contact with me. Thanks!

# Support
You can support me, development of AgenticCore and my other projects [here.](https://buymeacoffee.com/myusuf "here.") Any donation is appreciated!
