# Quickstart
This quick start guide will help you get up and running with Send to Unreal.

First thing you need to do is download the latest versioned zip file from the [releases page](https://github.com/EpicGames/BlenderTools/releases?q=Send+to+unreal&expanded=true)
under the `Assets` dropdown. The zip file name will start with `send2ue`.

::: tip Note
   If you get a 404 error when you click the link above, then you will need to sign in to your github account and link
it with your Epic Games account. Here is a [link with instructions](https://www.unrealengine.com/en-US/ue4-on-github)
on how to link your accounts.
:::

Next install the addon in Blender. Go to `Edit > Preferences` then to the addons tab. Click `install`.

![1](./images/1.png)

Go to the location where you downloaded your addon on disk and install the zip file.

![2](./images/2.png)

Now search for the addon and activate it.

![3](./images/3.png)

You'll notice when you activate it. This pipeline menu gets built.

![4](./images/4.png)

Next, you'll need to configure your unreal project (or verify that your project settings are already correct).
So let's walk through an example with a new project. First, open Unreal and create a new project.
Once your project is open, go to `Edit > Plugins`.

![5](./images/5.png)

Search for the "Python Editor Script Plugin" and enable it. Also ensure that the "Editor Scripting Utilities Plugin" is
already enabled.

![6](./images/6.png)

If you are also working with groom assets and would like to export alembic files from blender as unreal groom assets,
make sure to also have the plugins "Alembic Groom Importer" and "Groom" enabled.

![6_1](./images/6_1.png)

Additionally, make sure the "Support Compute Skin Cache" setting is turned on in Project Settings > Engine > Rendering > Optimizations.
This ensures grooms to render properly when bound to a skeletal mesh.

![16](./images/16.png)

Once you have enabled the plugins and project settings, you'll be prompted to restart the editor. Go ahead and restart. Once you've restarted, go to `Edit > Project Settings`.

![7](./images/7.png)

Search for "python" and then enable remote execution. Now Send to Unreal will work with your new Unreal project.

![8](./images/8.png)

Another thing that is useful to enable under `Edit > Editor Preferences`

![9](./images/9.png)

Search for "CPU", then under Editor Performance disable "Use Less CPU when in Background".
That way unreal continues to update even when it is not the active application, which means the Unreal user interface
will update constantly, and you will see your changes update without having to click on the Unreal Editor.

![10](./images/10.png)

Now lets run through a basic example with the default cube in your Blender scene.

![11](./images/11.png)

A simple test we can try in Blender to make sure this is working is move our cube to our `Export` collection.

![12](./images/12.png)

Click `Pipeline > Export > Send to Unreal`.

![13](./images/13.png)


::: tip Note
  On Windows, if you see a security alert, go ahead and allow Blender on your private network.
:::

You should now see the cube in unreal under `/untitled category/untitled asset/Cube`.

![14](./images/14.png)


Congrats, Send to Unreal is now working! To customize Send to Unreal to your needs, go to
`Pipeline > Export > Settings Dialog`. Here you can customize the paths for exports and imports
as well as the export and import settings, and validations.

<img src="./images/15.png" alt="15" width="450"/>
