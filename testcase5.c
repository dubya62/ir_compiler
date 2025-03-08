


int main(int argc, char** argv){
    int a = 2;
    int b;
    switch (a){
        case 1:
        case 3:
            break;
        case 4:
        case 5:
            b = 3;
            break;
        default:
            b = 2;
    }
    
    return 0;
}
