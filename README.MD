# README
<br>

This fork is being updated by Woeful_Wolf in an attempt to update Nier2Blend for Blender 2.80.
Currently only mesh data and armatures are supported and importing materials/textures have been disabled as it needs <br>
to be redone due to the new Blender 2.80 rendering updates.

## What is nier2blender?

* A blender plugin for import "Nier:Automata" .wmb file to blender with official rig<br>
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

## TO_DO
* PBR materials support
* motion parse and import

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
