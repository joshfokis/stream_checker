package main

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/parnurzeal/gorequest"
)

type Arrer interface {
	getMedia()
	setMonitor()
	removeMedia()
}

type Arr struct {
	host        string
	apikey      string
	mediaType   string
	url         string
	removeMedia bool
}

type Config struct {
	SONARR_HOST   string
	SONARR_APIKEY string
	RADARR_HOST   string
	RADARR_APIKEY string
	TMDB_APIKEY   string
	MY_SERVICES   []string
	COUNTRY       string
	REMOVE_MEDIA  bool
}

func (x Arr) getMedia() string {
	r_url := fmt.Sprintf("%s%s?apikey=%s", x.url, x.mediaType, x.apikey)

	_, body, errs := gorequest.New().
		Get(r_url).AppendHeader("Accept", "application/json").End()

	if errs != nil {
		fmt.Println(errs)
	}
	fmt.Println(r_url)
	return body
}

func loadConfig() Config {
	var config Config
	configFile, err := os.Open("config.json")

	if err != nil {
		fmt.Println(err)
	}

	defer configFile.Close()

	jsonparser := json.NewDecoder(configFile)
	jsonparser.Decode(&config)

	return config
}

func main() {
	c := loadConfig()
	radarr := Arr{
		c.RADARR_HOST,
		c.RADARR_APIKEY,
		"movie",
		fmt.Sprintf("http://%s/api/v3/", c.RADARR_HOST),
		c.REMOVE_MEDIA,
	}
	fmt.Println(radarr.apikey)
	media := radarr.getMedia()
	// media := getMedia("http://192.168.68.61:7878/api/v3/movie?apikey=d6d7eb4e64534f018f748d0acb222332")
	fmt.Println(media)
}
