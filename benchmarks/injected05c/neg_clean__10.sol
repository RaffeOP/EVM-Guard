pragma solidity 0.5.12;

contract Safe5782 {
    address public owner;
    uint256 public reserve;
    mapping(address => uint256) public deposits;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        deposits[msg.sender] += msg.value;
        reserve += msg.value;
    }
}
