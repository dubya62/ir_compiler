

int main(int argc, char** argv){
    int j=0;
    for (int i=0; i<10; i++){
        if (j > 3){
            continue;
        }
        j++;
    }
    return 0;
}
