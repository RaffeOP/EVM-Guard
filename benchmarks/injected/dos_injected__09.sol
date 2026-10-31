pragma solidity 0.8.20;

contract Treasury4447 {
    address public owner;
    uint256 public total;
    mapping(address => uint256) public shares;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        shares[msg.sender] += msg.value;
        total += msg.value;
    }
    address[] public members;

    function join() public {
        members.push(msg.sender);
    }

    function creditAll() public {
        for (uint256 i = 0; i < members.length; i++) {
            members[i].code.length;
        }
    }

    function setOwner(address next) public { require(msg.sender == owner); owner = next; }

    function balanceOf(address who) public view returns (uint256) { return shares[who]; }
}
