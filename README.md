# Blender2Nier

## VERY IMPORTANT
My addon Nier2Blender_2.8 is a REQUIREMENT. Without it, nothing will work, you will understand why. <br>
https://github.com/WoefulWolf/Nier2Blender_2.8

## Tutorials and a Proper Readme will come, eventually.
#### For now you should just understand these basic rules:
* Any model you wish to edit or replace must first be imported using my above-mentioned addon WITH materials/shaders. Thus DTT import is recommended to have it do everything automatically for you. <br>
* THINGS YOU SHOULD NOT CHANGE (unless you know what you are doing) include object names, material names, armatures, vertex groups or any custom properties on objects, materials, bones, armatures, etc. <br>
* An object cannot have more than one material. (Thus using the original from import is recommended, textures are separate). <br>
* All unused materials should be purged before export (something I might fix in the future, but not a priority). <br>
* When working with bone weights, one vertex cannot belong to more than 4 groups (in other words have weights belonging to more than 4 bones) <br>
* All meshes must be triangulated. (This gets done automatically, but you can do it yourself to ensure no unexpected results.) <br>
* After exporting, in-game the model might sometimes have flipped normals - you will have to flip them in Blender and re-export, sorry. <br>
* Open the Blender Console Window when exporting, this allows you to see its progress and any export errors. <br>
