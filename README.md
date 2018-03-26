# Activities/LetterMatch - Sugar Labs

## About Letter Match

![LetterMatchicon.png](docs/LetterMatchicon.png "LetterMatchicon.png")

Letter Match is an activity for introducing the Spanish vowels. It displays letters and images and associated sound files, such as 'A as in ave'. There are two modes:

1. See a letter, then click on the corresponding picture.
2. See a picture, then click on the corresponding letter.

(Also see [AEIOU](https://github.com/sugarlabs/AEIOU), [I Can Read](https://github.com/sugarlabs/i-can-read-activity), and [I Know My ABCs](https://github.com/sugarlabs/iknowmyabcs))

## Where to get Letter Match

The Letter Match activity is available for download from the [Sugar Activity Library](http://activities.sugarlabs.org): [Letter Match](http://activities.sugarlabs.org/en-US/sugar/addon/4627)

The source code is available on [GitHub](https://github.com/sugarlabs/lettermatch)

## Using Letter Match

| ![](docs/180px-LetterMatch.png "180px-LetterMatch.png") | ![](docs/180px-LetterMatch2.png "180px-LetterMatch2.png")| ![](docs/180px-LetterMatch3.png "180px-LetterMatch3.png") |
|---|---|---|
| Letter game | Picture game | Customization panel |

### Toolbars

![LetterMatchToolbar.png](docs/LetterMatchToolbar.png "LetterMatchToolbar.png")

Activity toolbar
:  Change the activity name; add notes to the Sugar Journal

Custom toolbar
:  Used to add new pictures and sounds

Letter mode
: See a letter and choose a picture

Picture mode
: See a picture and choose a letter

Stop button
: Exit the activity

![LetterMatchCustomToolbar.png](docs/LetterMatchCustomToolbar.png "LetterMatchCustomToolbar.png")

Load picture
: Load a new picture from the Sugar Journal

Load sound
: Load a new sound from the Sugar Journal

Letter entry
:  Enter the letter of the alphabet associated with these pictures and sounds

Add button
:  Add the picture and image to the database

## Learning with Letter Match

While far from contructionist, this activity does provide a mechanism for learning the alphabet.

## Modifying Letter Match

As of Version 3, only a Spanish version is included. In order to add other languages, we need:

* Audio recordings of the letter names.
* Audio recordings of the picture names.
* Perhaps additional pictures, in order ensure there is a picture for each letter of the alphabet.

There is a language-specific database file maintained in ./lessons/??/alphabet.csv where ?? is the 2-digit language code. The format of the CSV file is:

|  letter  |  word  |  color (#RRGGBB) |  image file  |  sound file (image)  |  sound file (letter)  |
|---|---|---|---|---|---|
| R  |  (r)atón  |  #F08020  |  raton.png  |  raton.ogg  |  r.ogg  |

## Extending Letter Match

Using the customization toolbar, it is possible for the learner to add their own pictures and sound recordings.

## Where to report problems

You are welcome to leave comments/suggestions on the [sugarlabs/lettermatch/issues](https://github.com/sugarlabs/lettermatch/issues) page.

## Credits

Letter Match was written and is maintained by [User:Walter](https://wiki.sugarlabs.org/go/User%3AWalter "User:Walter"). He was inspired in part by the work of Maria Perez, Fundación Zamora Terán. [Aneesh Dogra](https://wiki.sugarlabs.org/go/Aneesh_Dogra "Aneesh Dogra"
) added the customization toolbar.
