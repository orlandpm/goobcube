sudo apt update
sudo apt install fluidsynth
sudo apt install libsdl2-ttf-2.0-0

mkdir -p ./soundfonts
curl -L -o ./soundfonts/FluidR3_GM.sf2 https://github.com/urish/cppfluid/raw/master/examples/FluidR3_GM.sf2