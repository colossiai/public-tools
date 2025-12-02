package main

import (
	"encoding/json"
	"net/http"
	"time"
)

type CommonResp[T any] struct {
	Code    int    `json:"code"`
	Message string `json:"message"`
	Data    T      `json:"data"`
}

type GenericApiClient struct {
	baseUrl    string
	apiKey     string
	privateKey string
	httpClient *http.Client
}

func NewGenericClient(baseUrl, apiKey, privateKey string) *GenericApiClient {
	return &GenericApiClient{
		baseUrl:    baseUrl,
		apiKey:     apiKey,
		privateKey: privateKey,
		httpClient: &http.Client{Timeout: time.Second * 5},
	}
}

// if returned `err` is bu.AppError, it means server return valid JSON with error code, otherwise it should be IO error
func invokeApi[T any](client *GenericApiClient, apiPath string, param any) (*CommonResp[T], error) {
	data := jsonlib.Compact(param)
	timestampSec := time.Now().Unix()
	sign := calcSignature(data, client.apiKey, client.privateKey, timestampSec)
	body := map[string]any{
		"api_key":   client.apiKey,
		"version":   SsApiVersion,
		"timestamp": timestampSec,
		"data":      data,
		"sign":      sign,
	}

	url := client.baseUrl + apiPath
	bodyStr := jsonlib.Compact(body)

	rawResp, err := mylib.DoHttp(client.httpClient, ssHttpMethod, url, ssHttpHeaders, bodyStr)
	if err != nil {
		return nil, err
	}

	var resp CommonResp[T]
	if err := json.Unmarshal(rawResp.Content, &resp); err != nil {
		return nil, err
	}
	if !resp.IsSuccess() {
		return nil, mylib.NewAppError(resp.Code, resp.Message)
	}
	return &resp, nil
}

func (client *GenericApiClient) GetEndpoint() (*CommonResp[*string], error) {
	return invokeApi[*string](client, "/data", nil)
}
