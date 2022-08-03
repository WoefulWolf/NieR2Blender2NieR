![NieR2Blender2NieR](https://i.imgur.com/vdkqt8S.png) <br>
(Amazing banner created by [@IntonerAlice](https://twitter.com/IntonerAlice))
## VERY IMPORTANT
This is the full combination tools of NieR2Blender and Blender2NieR, from now on known as NieR2Blender2NieR. <br>
THIS IS ALSO STILL IN DEVELOPMENT BUT IS AS STABLE AS IT CURRENTLY CAN BE. If any updates break something that worked in the past, please let me know immediately. Every update is intended to be fully functional, the next just better than the prior. <br>
<br>
If you use the tool and release something, please give appropriate credit and info. I would really love for the tools to become more 
widely known so that others can start modding too. :)
<br> <br>
**We still have much more to share, but we are trying to get this out as fast as possible, expect much more documentation incoming. And things to become easier.**

## Installation Instructions:
1. Install [Blender](https://www.blender.org/) (also available on Steam).
2. Download this repository as a ZIP (Green button labelled "Code" near the top-right, `Download ZIP`).
3. Launch Blender.
4. Go to `Edit > Preferences`.
5. Go to the `Add-ons` section and press `Install...` near the top-right.
6. Select the ZIP you downloaded in step 2 and press `Install Add-on`.
7. Check the tickbox next to `Import-Export: Nier2Blender2NieR (NieR:Automata Data Exporter)`.

## Some Tips:
#### For now, you should just understand these basic things:
* ~~You can find info/tutorials at the wiki (near top of this page) [SORTA OUTDATED]~~.
* ~~Watch https://youtu.be/Mr-zmXAwM5g for a very basic example video [OUTDATED]~~.
* Visit our [NieR:Modding](https://discord.gg/7F76ZVv) community Discord server for help.
* Start by importing an asset you would like to modify/append to.
* An object cannot have more than one material. (Thus using the original from import is recommended, textures are separate). <br>
* When working with bone weights, one vertex cannot belong to more than 4 groups (in other words have weights belonging to more than 4 bones) <br>
* All meshes must be triangulated. (This gets done automatically, but you can do it yourself to ensure no unexpected results.) <br>
* Open the Blender Console Window when exporting, this allows you to see its progress and any export errors. <br>
* A lot of my code is put together with duct-tape and instant ramen, thus it is unoptimized, ugly and straight up fucked at places. :)

## WTP & WTA Setup (Textures/Shaders)
* The WTP/WTA Exporter can be found under the "Output" tab of the "Properties" window (the "printer" icon).
* (This is one automatically assuming your file structure is fine). I recommend loading the original textures before adding/replacing with custom ones. To do this, use the "Select Textures Directory" option and load the "textures" folder created when importing a model (*/nier2blender_extracted/######.dtt/textures/*)
* After adding or changing a unique texture identifier, make sure to "Sync Identifiers in Materials" before exporting a WMB.
* Leave texture paths set to "None" if the map is unused.

## Exporting For NieR:Automata
* The full exporter can be found under the "Output" tab of the "Properties" window (the "printer" icon).
* Make sure you have the required metadata files also located in the folder you wish to pack (metadata files are generated when importing a DAT/DTT and can be found the nier2blender_extracted directories).
* The One-Click Exporter is highly recommended to save you time!
* WMB & WTP is packed in the DTT. Other files (like the WTA) is packed in the DAT.
 
## Bug Reports and Contact
* Please leave bug reports. You can leave them here on the GitHub under issues. Remember to post as much info as you can. <br>
* Feel free to contact me for any questions or issues you might be having. You can contact me, and some other members of the NieR:Modding community at our Discord server: https://discord.gg/7F76ZVv

# GL HF!

## THANKS:
* RaiderB, the newest gigachad crew member.
* The wonderful people from Bayonetta Tools, namely Elediane.
* Kekoulis, literal months of support and help with testing.
* DevolasRevenge, for help with testing and the writing of wiki pages.
* The BONE boi Ameii.
* Comrade Petrarca. o7
* Martino.
* delle the texture man.
* Platinum Games.
* **Yoko Taro.**
