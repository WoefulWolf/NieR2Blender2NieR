![Nier2Blender](https://user-images.githubusercontent.com/54476280/64488614-519a7280-d24a-11e9-8627-784cdc5ac3de.png)
<br>

This fork is being updated by **Woeful_Wolf** in an attempt to keep Nier2Blender alive for Blender 2.8 and the future versions <br>

<br>

Materials/textures have been redone completely due to the new Blender 2.8 rendering engines updates. <br>
This means it now has **Eevee/Cycles material import support for the Principled Shader! PBR Yay!** <br>

<br>

This is still a bit WIP so reporting any bugs would be appreciated, I could not test with every model in the game but if you find any that are problematic, be sure to include what model it was (helps with debugging). <br>
<br>
If looking for the exporter, here it is: <br>
https://github.com/WoefulWolf/Blender2NieR
<br>
(And thanks for helping with testing; Kekoulis)

## What have I added exactly?

* Blender 2.8 Support
* Importing to Eevee/Cycles
* Alpha Channel Support
* MaskMap Support
* LightMap Support
* Multiple Normal Map Support
* Importing straight from .DTT files directly (skips manual extraction)
* (and probably some other small things I've forgotten)

<br>

## What is nier2blender?

* A blender plugin for import "Nier:Automata" .wmb (or now .dtt) file to blender with official rig<br>
* codes can only run with python3


<br>

## Usage

<br> 

#### dat_unpacker.py

* python dat_unpacker.py cpk_unpacked_folder your_extract_folder

* if you do not have python3 then execute it with blender in command line<br>
blender --background --python dat_unpacker.py cpk_unpacked_folder your_extract_folder

#### blender addons
* copy the whole repo foleder to blender addons folder and active it in blender preferences

<br>

## PS:

* #### PS1: Where to find .wmb files?
    wmb files are packed in .cpk files under the game data folder which can be unpack by CriPakTools.<br>
    unpack the .cpk files and find .dat and .dtt files both of them are necessary for extracting models<br>
    unpack .dat and .dtt files using dat_unpacker.py<br>
    .wmb files can be found in unpacked .dtt files<br>


* #### PS2: Put .dat and .dtt files in pair under the same folder
    .dat and .dtt file have the same name file name are paired<br>
    .dat file contains control information such material, motions of the model <br>
    .dtt file contains .wmb model and texture package<br>

* #### PS3：Useful folders in cpk
    /pl -> main character models<br>
    /wd -> scence models<br>
    /wp -> weapon models<br>
    /um -> npc models<br>
    /em -> enemy models<br>
    /et -> item models<br>

* #### PS4: Tips
    unpack all cpk files and merge them under the same forlder before unpack dat and dtt files

*  #### PS4 Pro:
    just a joke enjoy it.
